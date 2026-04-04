"""
URI - 统一资源标识符
基于 Claude Code uri.ts 设计

URI工具。
"""
import urllib.parse
from typing import Dict


def parse(url: str) -> Dict:
    """
    解析URL
    
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
    构建URL
    
    Args:
        scheme: 协议
        host: 主机
        path: 路径
        query: 查询字符串
        port: 端口
        fragment: 锚点
        
    Returns:
        URL字符串
    """
    if port:
        host = f"{host}:{port}"
    
    netloc = host
    if scheme:
        return f"{scheme}://{netloc}{path}?{query}#{fragment}".rstrip('#?')
    return f"{netloc}{path}"


def encode(value: str) -> str:
    """URL编码"""
    return urllib.parse.quote(value)


def decode(value: str) -> str:
    """URL解码"""
    return urllib.parse.unquote(value)


def encode_params(params: Dict) -> str:
    """
    编码参数
    
    Args:
        params: 参数字典
        
    Returns:
        查询字符串
    """
    return urllib.parse.urlencode(params)


def decode_params(query: str) -> Dict:
    """
    解码参数
    
    Args:
        query: 查询字符串
        
    Returns:
        参数字典
    """
    return dict(urllib.parse.parse_qsl(query))


def add_param(url: str, key: str, value: str) -> str:
    """
    添加参数到URL
    
    Args:
        url: URL
        key: 参数名
        value: 参数值
        
    Returns:
        新URL
    """
    parsed = urllib.parse.urlparse(url)
    params = decode_params(parsed.query)
    params[key] = value
    
    return urllib.parse.urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        encode_params(params),
        parsed.fragment
    ))


def remove_param(url: str, key: str) -> str:
    """
    从URL移除参数
    
    Args:
        url: URL
        key: 参数名
        
    Returns:
        新URL
    """
    parsed = urllib.parse.urlparse(url)
    params = decode_params(parsed.query)
    params.pop(key, None)
    
    return urllib.parse.urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        encode_params(params),
        parsed.fragment
    ))


# 导出
__all__ = [
    "parse",
    "build",
    "encode",
    "decode",
    "encode_params",
    "decode_params",
    "add_param",
    "remove_param",
]
