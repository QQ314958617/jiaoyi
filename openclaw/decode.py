"""
Decode - 解码
基于 Claude Code decode.ts 设计

解码工具。
"""
import base64
import json
import urllib.parse
from typing import Any, Dict


def json_decode(data: str) -> Any:
    """
    JSON解码
    
    Args:
        data: JSON字符串
        
    Returns:
        解码后的对象
    """
    return json.loads(data)


def json_encode(data: Any) -> str:
    """
    JSON编码
    
    Args:
        data: 对象
        
    Returns:
        JSON字符串
    """
    return json.dumps(data)


def json_pretty(data: Any, indent: int = 2) -> str:
    """
    格式化JSON
    
    Args:
        data: 对象
        indent: 缩进
        
    Returns:
        格式化的JSON字符串
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def base64_decode(data: str) -> bytes:
    """Base64解码"""
    return base64.b64decode(data)


def base64_encode(data: bytes) -> str:
    """Base64编码"""
    return base64.b64encode(data).decode()


def url_decode(data: str) -> str:
    """URL解码"""
    return urllib.parse.unquote(data)


def url_encode(data: str) -> str:
    """URL编码"""
    return urllib.parse.quote(data)


def url_decode_params(query: str) -> Dict[str, str]:
    """
    URL参数解码
    
    Args:
        query: 查询字符串
        
    Returns:
        参数字典
    """
    return dict(urllib.parse.parse_qsl(query))


def url_encode_params(params: Dict) -> str:
    """
    URL参数编码
    
    Args:
        params: 参数字典
        
    Returns:
        查询字符串
    """
    return urllib.parse.urlencode(params)


def html_decode(data: str) -> str:
    """HTML实体解码"""
    import html
    return html.unescape(data)


def html_encode(data: str) -> str:
    """HTML实体编码"""
    import html
    return html.escape(data)


# 导出
__all__ = [
    "json_decode",
    "json_encode",
    "json_pretty",
    "base64_decode",
    "base64_encode",
    "url_decode",
    "url_encode",
    "url_decode_params",
    "url_encode_params",
    "html_decode",
    "html_encode",
]
