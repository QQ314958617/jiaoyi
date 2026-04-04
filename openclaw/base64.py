"""
Base64 - Base64编码
基于 Claude Code base64.ts 设计

Base64工具。
"""
import base64 as _base64


def encode(data: Union[bytes, str]) -> str:
    """
    Base64编码
    
    Args:
        data: 字符串或字节
        
    Returns:
        Base64字符串
    """
    if isinstance(data, str):
        data = data.encode()
    return _base64.b64encode(data).decode()


def decode(data: str) -> bytes:
    """
    Base64解码
    
    Args:
        data: Base64字符串
        
    Returns:
        原始字节
    """
    # 补全padding
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return _base64.b64decode(data)


def encode_url(data: Union[bytes, str]) -> str:
    """
    URL安全的Base64编码
    
    Args:
        data: 字符串或字节
        
    Returns:
        Base64字符串
    """
    if isinstance(data, str):
        data = data.encode()
    return _base64.urlsafe_b64encode(data).decode().rstrip('=')


def decode_url(data: str) -> bytes:
    """
    URL安全的Base64解码
    
    Args:
        data: Base64字符串
        
    Returns:
        原始字节
    """
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return _base64.urlsafe_b64decode(data)


def to_string(data: bytes) -> str:
    """Base64转字符串"""
    return decode(data).decode('utf-8')


def from_string(text: str) -> str:
    """字符串转Base64"""
    return encode(text.encode('utf-8'))


# 导出
__all__ = [
    "encode",
    "decode",
    "encode_url",
    "decode_url",
    "to_string",
    "from_string",
]
