"""
OpenClaw Preconnect
====================
Inspired by Claude Code's src/utils/apiPreconnect.ts.

核心功能：
1. 预热 HTTP 连接（TCP+TLS 握手）
2. 连接池复用
3. DNS 预解析

原理：
- 第一次真实请求需要 TCP+TLS 握手（~100-200ms）
- 预连接让握手在后台完成，和业务逻辑并行
- 真正的请求复用预热的连接，零延迟

用途：
- 预热 MiniMax API 连接
- 预热行情数据 API 连接
- 交易时段开始前预热所有数据源
"""

from __future__ import annotations

import socket
import ssl
import threading
import time
from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from urllib.parse import urlparse


# ============================================================================
# 连接状态
# ============================================================================

@dataclass
class ConnectionState:
    """连接状态"""
    host: str
    port: int
    scheme: str
    connected: bool = False
    connecting: bool = False
    last_used: float = 0.0
    latency_ms: float = 0.0


# ============================================================================
# HTTP 预热器
# ============================================================================

class HTTPWarmer:
    """
    HTTP 连接预热器。

    对应 Claude Code 的 preconnectAnthropicApi()。

    用法：
        warmer = HTTPWarmer()
        warmer.preconnect("https://api.minimax.chat")
        # 后台：DNS + TCP + TLS 握手并行
        # ... later ...
        result = requests.get("https://api.minimax.chat/...")  # 复用连接，零延迟
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self._connections: Dict[str, ConnectionState] = {}
        self._lock = threading.Lock()
        self._fired: Set[str] = set()  # 已预热的 host:port

    def preconnect(self, url: str, background: bool = True) -> bool:
        """
        预热到 URL 的连接。

        Args:
            url: 完整的 URL 或只是 host
            background: 是否后台执行（不阻塞）

        Returns:
            True 如果发起预热，False 如果已预热或无效 URL
        """
        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        scheme = parsed.scheme or "https"
        key = f"{host}:{port}"

        with self._lock:
            if key in self._fired:
                return False  # 已预热
            self._fired.add(key)

        if background:
            t = threading.Thread(target=self._do_connect, args=(host, port, scheme), daemon=True)
            t.start()
            return True
        else:
            return self._do_connect(host, port, scheme)

    def preconnect_batch(self, urls: list, background: bool = True) -> None:
        """批量预热"""
        for url in urls:
            self.preconnect(url, background=background)

    def _do_connect(self, host: str, port: int, scheme: str) -> bool:
        """执行连接"""
        key = f"{host}:{port}"
        start = time.time()

        try:
            if scheme == "https":
                ctx = ssl.create_default_context()
                with socket.create_connection((host, port), timeout=self.timeout) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                        latency = (time.time() - start) * 1000
                        with self._lock:
                            self._connections[key] = ConnectionState(
                                host=host,
                                port=port,
                                scheme=scheme,
                                connected=True,
                                connecting=False,
                                last_used=time.time(),
                                latency_ms=latency,
                            )
                        return True
            else:
                with socket.create_connection((host, port), timeout=self.timeout) as sock:
                    latency = (time.time() - start) * 1000
                    with self._lock:
                        self._connections[key] = ConnectionState(
                            host=host,
                            port=port,
                            scheme=scheme,
                            connected=True,
                            connecting=False,
                            last_used=time.time(),
                            latency_ms=latency,
                        )
                    return True

        except Exception as e:
            # 连接失败，移除 fired 标记，允许重试
            with self._lock:
                self._fired.discard(key)
            return False

    def is_connected(self, url_or_host: str) -> bool:
        """检查是否已预热"""
        parsed = urlparse(url_or_host)
        host = parsed.hostname or url_or_host
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        key = f"{host}:{port}"

        with self._lock:
            return key in self._fired

    def get_stats(self) -> Dict:
        """获取连接统计"""
        with self._lock:
            return {
                "preheated": len(self._fired),
                "active": sum(1 for c in self._connections.values() if c.connected),
                "connections": {
                    key: {
                        "host": c.host,
                        "latency_ms": round(c.latency_ms, 1),
                        "last_used": c.last_used,
                    }
                    for key, c in self._connections.items()
                }
            }


# ============================================================================
# DNS 预解析
# ============================================================================

class DNSResolver:
    """
    DNS 预解析器。

    提前解析域名，减少首次请求的 DNS 查询延迟。

    用法：
        resolver = DNSResolver()
        resolver.resolve("api.minimax.chat")
        resolver.resolve_batch([
            "api.minimax.chat",
            "stockapi.example.com",
        ])
    """

    def __init__(self):
        self._cache: Dict[str, list] = {}  # hostname -> IPs
        self._lock = threading.Lock()

    def resolve(self, hostname: str, background: bool = True) -> Optional[list]:
        """
        解析域名。

        Returns:
            IP 列表或 None（如果失败）
        """
        with self._lock:
            if hostname in self._cache:
                return self._cache[hostname]

        if background:
            t = threading.Thread(target=self._do_resolve, args=(hostname,), daemon=True)
            t.start()
            return None
        else:
            return self._do_resolve(hostname)

    def _do_resolve(self, hostname: str) -> Optional[list]:
        try:
            result = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            ips = list(set(r[4][0] for r in result))
            with self._lock:
                self._cache[hostname] = ips
            return ips
        except Exception:
            return None

    def resolve_batch(self, hostnames: list, background: bool = True) -> None:
        """批量解析"""
        for hostname in hostnames:
            self.resolve(hostname, background=background)


# ============================================================================
# 全局实例
# ============================================================================

_http_warmer: Optional[HTTPWarmer] = None
_dns_resolver: Optional[DNSResolver] = None
_global_lock = threading.Lock()


def get_http_warmer() -> HTTPWarmer:
    global _http_warmer
    if _http_warmer is None:
        with _global_lock:
            if _http_warmer is None:
                _http_warmer = HTTPWarmer()
    return _http_warmer


def get_dns_resolver() -> DNSResolver:
    global _dns_resolver
    if _dns_resolver is None:
        with _global_lock:
            if _dns_resolver is None:
                _dns_resolver = DNSResolver()
    return _dns_resolver


# ============================================================================
# 便捷函数
# ============================================================================

def preconnect(url: str, background: bool = True) -> bool:
    """预热 HTTP 连接"""
    return get_http_warmer().preconnect(url, background=background)


def preconnect_batch(urls: list, background: bool = True) -> None:
    """批量预热"""
    get_http_warmer().preconnect_batch(urls, background=background)


def resolve_dns(hostname: str, background: bool = True) -> Optional[list]:
    """DNS 预解析"""
    return get_dns_resolver().resolve(hostname, background=background)


# ============================================================================
# 交易系统常用预热
# ============================================================================

TRADING_PRECONNECT_URLS = [
    "https://api.minimax.chat",      # MiniMax AI API
    "https://qt.gtimg.cn",           # 腾讯财经行情
    "https://web.ifzq.gtimg.cn",     # 行情API
]


def preconnect_trading_apis() -> None:
    """
    预热交易系统常用的 API 连接。

    在交易时段开始前调用（如 09:00 前）。
    让 DNS + TCP + TLS 在后台完成。
    """
    preconnect_batch(TRADING_PRECONNECT_URLS, background=True)
