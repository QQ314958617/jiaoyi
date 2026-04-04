"""
URI - URI工具
基于 Claude Code uri.ts 设计

URI处理工具。
"""
import urllib.parse
from typing import Dict


def parse(url: str) -> Dict:
    """
    解析URI
    
    Args:
        url: URL字符串
        
    Returns:
        分解的URL部分
    """
    parsed = urllib.parse.urlparse(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path,
        "query": parsed.query,
        "fragment": parsed.fragment,
        "username": parsed.username,
        "password": parsed.password,
    }


def build(scheme: str = "", host: str = "", path: str = "",
          query: str = "", port: int = None, fragment: str = "") -> str:
    """
    构建URI
    
    Returns:
        URI字符串
    """
    if port:
        host = f"{host}:{port}"
    
    netloc = host
    result = ""
    if scheme:
        result = f"{scheme}://{netloc}"
    result += path
    if query:
        result += f"?{query}"
    if fragment:
        result += f"#{fragment}"
    return result


def encode(value: str) -> str:
    """URL编码"""
    return urllib.parse.quote(value)


def decode(value: str) -> str:
    """URL解码"""
    return urllib.parse.unquote(value)


def encode_params(params: Dict) -> str:
    """编码查询参数"""
    return urllib.parse.urlencode(params)


def decode_params(query: str) -> Dict:
    """解码查询参数"""
    return dict(urllib.parse.parse_qsl(query))


# 导出
__all__ = [
    "parse",
    "build",
    "encode",
    "decode",
    "encode_params",
    "decode_params",
]
