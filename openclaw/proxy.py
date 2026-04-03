"""
OpenClaw HTTP Proxy Client
==========================
Inspired by Claude Code's src/upstreamproxy/upstreamproxy.ts (285 lines).

HTTP(S) 代理客户端，支持：
1. CONNECT 方法（建立隧道）
2. HTTP 隧道（用于 HTTPS）
3. 代理认证
4. 自动选择直连/代理

Claude Code 模式：
- NO_PROXY_LIST: 跳过代理的地址
- SSL_CERT_FILE: 代理 CA 证书
- fail_open: 代理失败不影响主流程

对于交易系统：用于：
- 调用行情 API 时走代理
- 避免行情数据 IP 限制
- 隐藏真实 IP
"""

from __future__ import annotations

import socket, ssl, threading
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse

# ============================================================================
# 常量
# ============================================================================

# 默认跳过代理的地址
NO_PROXY_LIST = [
    "localhost", "127.0.0.1", "::1",
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
    "169.254.0.0/16",  # AWS IMDS
]

@dataclass
class ProxyConfig:
    """代理配置"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    # 跳过代理的地址（支持通配符）
    no_proxy: Optional[List[str]] = None

# ============================================================================
# 代理客户端
# ============================================================================

class ProxyClient:
    """
    HTTP 代理客户端
    
    支持：
    - HTTP 代理（直接转发）
    - HTTPS 隧道（CONNECT 方法）
    - 代理认证
    - NO_PROXY 列表
    
    Claude Code fail_open 设计：
    - 代理连接失败 → 回退到直连
    - 代理超时 → 回退到直连
    """
    
    def __init__(self, config: Optional[ProxyConfig] = None):
        self.config = config
        self._lock = threading.Lock()
        self._tunnel_cache: Dict[str, socket.socket] = {}
    
    def should_proxy(self, host: str, port: int) -> bool:
        """判断是否应该走代理"""
        if not self.config:
            return False
        
        # 检查 NO_PROXY
        if self.config.no_proxy:
            for pattern in self.config.no_proxy:
                if self._match_no_proxy(host, pattern):
                    return False
        
        return True
    
    def _match_no_proxy(self, host: str, pattern: str) -> bool:
        """检查 host 是否匹配 NO_PROXY 模式"""
        # 精确匹配
        if host == pattern:
            return True
        
        # 通配符匹配 *.example.com
        if pattern.startswith("*."):
            domain = pattern[2:]
            return host.endswith(domain) or host == domain[1:]
        
        # 前缀匹配
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return host.startswith(prefix)
        
        # 后缀匹配
        if pattern.startswith("*"):
            suffix = pattern[1:]
            return host.endswith(suffix)
        
        return False
    
    def _build_auth_header(self) -> Optional[str]:
        """构建代理认证头"""
        if not self.config or not self.config.username:
            return None
        
        import base64
        creds = f"{self.config.username}:{self.config.password or ''}"
        return "Basic " + base64.b64encode(creds.encode()).decode()
    
    def connect_tunnel(self, host: str, port: int, 
                       timeout: float = 10.0) -> socket.socket:
        """
        建立 HTTPS 隧道（CONNECT 方法）
        
        流程：
        1. 连接代理服务器
        2. 发送 CONNECT host:port HTTP/1.1
        3. 等待 200 Connection Established
        4. 返回升级后的 socket
        """
        cache_key = f"{host}:{port}"
        
        with self._lock:
            if cache_key in self._tunnel_cache:
                s = self._tunnel_cache[cache_key]
                # 检查连接是否还活着
                try:
                    s.settimeout(0.1)
                    s.recv(1)
                    # 连接已断开
                    del self._tunnel_cache[cache_key]
                except:
                    # 连接可用
                    return s
        
        if not self.config:
            # 直连
            return self._direct_connect(host, port, timeout)
        
        # 连接代理
        proxy = self.config
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        try:
            sock.connect((proxy.host, proxy.port))
            
            # 发送 CONNECT 请求
            request = f"CONNECT {host}:{port} HTTP/1.1\r\n"
            request += f"Host: {host}:{port}\r\n"
            
            auth = self._build_auth_header()
            if auth:
                request += f"Proxy-Authorization: {auth}\r\n"
            
            request += "\r\n"
            sock.sendall(request.encode())
            
            # 读取响应
            response = b""
            while b"\r\n\r\n" not in response:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
            
            # 检查是否是 200
            status_line = response.split(b"\r\n")[0].decode("ascii", errors="ignore")
            if "200" not in status_line:
                raise RuntimeError(f"Proxy CONNECT failed: {status_line}")
            
            # 升级为 SSL socket
            context = ssl.create_default_context()
            ssl_sock = context.wrap_socket(sock, server_hostname=host)
            
            with self._lock:
                self._tunnel_cache[cache_key] = ssl_sock
            
            return ssl_sock
            
        except Exception as e:
            sock.close()
            # fail_open: 代理失败，回退到直连
            return self._direct_connect(host, port, timeout)
    
    def _direct_connect(self, host: str, port: int, 
                        timeout: float = 10.0) -> socket.socket:
        """直连"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        # 升级为 SSL
        context = ssl.create_default_context()
        return context.wrap_socket(sock, server_hostname=host)
    
    def send_request(self, method: str, url: str, 
                     headers: Optional[Dict[str, str]] = None,
                     body: Optional[bytes] = None,
                     timeout: float = 30.0) -> Tuple[int, Dict, bytes]:
        """
        发送 HTTP 请求（自动选择直连或代理）
        
        返回: (status_code, headers, body)
        """
        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        
        if self.should_proxy(host, port) and parsed.scheme == "https":
            # HTTPS: 使用隧道
            sock = self.connect_tunnel(host, port, timeout)
            is_ssl = True
        elif self.should_proxy(host, port):
            # HTTP: 直接转发
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.config.host, self.config.port))
            is_ssl = False
        else:
            # 直连
            sock = self._direct_connect(host, port, timeout)
            is_ssl = True
        
        try:
            # 构建请求
            request = f"{method} {path} HTTP/1.1\r\n"
            request += f"Host: {host}:{port}\r\n"
            
            if headers:
                for k, v in headers.items():
                    if k.lower() not in ("host", "connection"):
                        request += f"{k}: {v}\r\n"
            
            if body:
                request += f"Content-Length: {len(body)}\r\n"
            
            request += "\r\n"
            sock.sendall(request.encode())
            
            if body:
                sock.sendall(body)
            
            # 读取响应
            response = b""
            while True:
                try:
                    data = sock.recv(8192)
                    if not data:
                        break
                    response += data
                    # 完整响应
                    if b"\r\n\r\n" in response:
                        # 检测 chunked 或完整
                        if b"Content-Length:" in response or b"content-length:" in response:
                            break
                        if b"0\r\n\r\n" in response:
                            break
                except socket.timeout:
                    break
            
            # 解析状态行
            lines = response.split(b"\r\n")
            status_line = lines[0].decode("ascii", errors="ignore")
            parts = status_line.split(" ")
            status_code = int(parts[1]) if len(parts) > 1 else 200
            
            # 找到 header 结束位置
            header_end = response.find(b"\r\n\r\n")
            if header_end >= 0:
                header_part = response[:header_end].decode("ascii", errors="ignore")
                body_start = header_end + 4
            else:
                header_part = ""
                body_start = len(lines[0]) + 2
            
            # 解析 headers
            resp_headers = {}
            for line in header_part.split("\r\n")[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    resp_headers[k.strip().lower()] = v.strip()
            
            body = response[body_start:]
            
            return status_code, resp_headers, body
            
        finally:
            sock.close()
    
    def close(self) -> None:
        """关闭所有隧道"""
        with self._lock:
            for sock in self._tunnel_cache.values():
                try:
                    sock.close()
                except:
                    pass
            self._tunnel_cache.clear()


# ============================================================================
# 全局实例管理
# ============================================================================

_proxy: Optional[ProxyClient] = None
_proxy_config: Optional[ProxyConfig] = None
_init_lock = threading.Lock()

def init_proxy(config: Optional[ProxyConfig] = None) -> None:
    """初始化代理配置"""
    global _proxy, _proxy_config
    with _init_lock:
        _proxy_config = config
        _proxy = ProxyClient(config)

def get_proxy() -> Optional[ProxyClient]:
    """获取全局代理客户端"""
    return _proxy

def is_proxy_enabled() -> bool:
    """代理是否启用"""
    return _proxy_config is not None
