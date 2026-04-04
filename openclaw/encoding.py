"""
Encoding - 编码工具
基于 Claude Code encoding.ts 设计

各种编码解码工具。
"""
import base64
import json
import urllib.parse
from typing import Any, Optional


def encode_base64(data: str) -> str:
    """
    Base64编码
    
    Args:
        data: 字符串
        
    Returns:
        Base64编码字符串
    """
    return base64.b64encode(data.encode()).decode()


def decode_base64(data: str) -> str:
    """
    Base64解码
    
    Args:
        data: Base64字符串
        
    Returns:
        原始字符串
    """
    return base64.b64decode(data.encode()).decode()


def encode_url(data: str) -> str:
    """
    URL编码
    
    Args:
        data: 字符串
        
    Returns:
        URL编码字符串
    """
    return urllib.parse.quote(data)


def decode_url(data: str) -> str:
    """
    URL解码
    
    Args:
        data: URL编码字符串
        
    Returns:
        原始字符串
    """
    return urllib.parse.unquote(data)


def encode_hex(data: str) -> str:
    """
    十六进制编码
    
    Args:
        data: 字符串
        
    Returns:
        十六进制编码字符串
    """
    return data.encode().hex()


def decode_hex(data: str) -> str:
    """
    十六进制解码
    
    Args:
        data: 十六进制字符串
        
    Returns:
        原始字符串
    """
    return bytes.fromhex(data).decode()


def encode_json(data: Any) -> str:
    """
    JSON编码
    
    Args:
        data: 对象
        
    Returns:
        JSON字符串
    """
    return json.dumps(data)


def decode_json(data: str) -> Any:
    """
    JSON解码
    
    Args:
        data: JSON字符串
        
    Returns:
        对象
    """
    return json.loads(data)


# 导出
__all__ = [
    "encode_base64",
    "decode_base64",
    "encode_url",
    "decode_url",
    "encode_hex",
    "decode_hex",
    "encode_json",
    "decode_json",
]
