"""
Url - URL工具
基于 Claude Code url.ts 设计

URL解析和构建工具。
"""
import urllib.parse
from typing import Dict, Optional


def parse(url: str) -> Dict[str, str]:
    """
    解析URL
    
    Returns:
        {"scheme": "https", "host": "example.com", "path": "/path", ...}
    """
    parsed = urllib.parse.urlparse(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "port": parsed.port,
        "path": parsed.path,
        "query": parsed.query,
        "fragment": parsed.fragment,
        "username": parsed.username,
        "password": parsed.password,
    }


def build(scheme: str = "https", host: str = "", path: str = "",
          query: Dict[str, str] = None, fragment: str = "") -> str:
    """
    构建URL
    
    Args:
        scheme: 协议
        host: 主机
        path: 路径
        query: 查询参数
        fragment: 锚点
    """
    if query:
        query_str = urllib.parse.urlencode(query)
    else:
        query_str = ""
    
    netloc = host
    if ":" in host and not host.startswith("["):
        # 处理IPv6
        pass
    
    return urllib.parse.urlunparse((
        scheme, netloc, path, "", query_str, fragment
    ))


def join(*parts: str) -> str:
    """
    拼接URL部分
    """
    result = []
    for part in parts:
        if not part:
            continue
        part = part.strip('/')
        result.append(part)
    
    return '/'.join(result)


def resolve(base: str, path: str) -> str:
    """
    解析相对路径
    
    Args:
        base: 基础URL
        path: 相对路径
    """
    if path.startswith('http://') or path.startswith('https://'):
        return path
    
    base_parsed = urllib.parse.urlparse(base)
    
    if path.startswith('/'):
        return urllib.parse.urlunparse((
            base_parsed.scheme, base_parsed.netloc, path, "", "", ""
        ))
    
    # 相对路径
    import os
    dir_path = os.path.dirname(base_parsed.path)
    new_path = join(dir_path, path)
    
    return urllib.parse.urlunparse((
        base_parsed.scheme, base_parsed.netloc, new_path, "", "", ""
    ))


def encode(text: str) -> str:
    """URL编码"""
    return urllib.parse.quote(text)


def decode(text: str) -> str:
    """URL解码"""
    return urllib.parse.unquote(text)


def encode_params(params: Dict[str, str]) -> str:
    """编码参数"""
    return urllib.parse.urlencode(params)


def decode_params(query: str) -> Dict[str, str]:
    """解码参数"""
    return dict(urllib.parse.parse_qsl(query))


def get_host(url: str) -> Optional[str]:
    """获取主机名"""
    return parse(url).get("host")


def get_path(url: str) -> str:
    """获取路径"""
    return parse(url).get("path", "/")


def is_absolute(url: str) -> bool:
    """是否为绝对URL"""
    return url.startswith('http://') or url.startswith('https://')


# 导出
__all__ = [
    "parse",
    "build",
    "join",
    "resolve",
    "encode",
    "decode",
    "encode_params",
    "decode_params",
    "get_host",
    "get_path",
    "is_absolute",
]
