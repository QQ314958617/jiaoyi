"""
Base64 - Base64编解码
基于 Claude Code base64.ts 设计

Base64工具。
"""
import base64 as _base64


def encode(data: str) -> str:
    """
    Base64编码
    
    Args:
        data: 字符串
        
    Returns:
        Base64编码字符串
    """
    return _base64.b64encode(data.encode()).decode()


def decode(data: str) -> str:
    """
    Base64解码
    
    Args:
        data: Base64字符串
        
    Returns:
        原始字符串
    """
    return _base64.b64decode(data.encode()).decode()


def encode_url_safe(data: str) -> str:
    """
    URL安全Base64编码
    
    Args:
        data: 字符串
        
    Returns:
        URL安全Base64字符串
    """
    return _base64.urlsafe_b64encode(data.encode()).decode().rstrip('=')


def decode_url_safe(data: str) -> str:
    """
    URL安全Base64解码
    
    Args:
        data: URL安全Base64字符串
        
    Returns:
        原始字符串
    """
    # 补齐padding
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    
    return _base64.urlsafe_b64decode(data.encode()).decode()


def encode_bytes(data: bytes) -> str:
    """
    字节数组Base64编码
    
    Args:
        data: 字节数据
        
    Returns:
        Base64字符串
    """
    return _base64.b64encode(data).decode()


def decode_bytes(data: str) -> bytes:
    """
    Base64解码为字节
    
    Args:
        data: Base64字符串
        
    Returns:
        字节数据
    """
    return _base64.b64decode(data.encode())


def encode_file(path: str) -> str:
    """
    文件内容Base64编码
    
    Args:
        path: 文件路径
        
    Returns:
        Base64字符串
    """
    with open(path, 'rb') as f:
        return _base64.b64encode(f.read()).decode()


def decode_to_file(data: str, path: str) -> None:
    """
    Base64解码写入文件
    
    Args:
        data: Base64字符串
        path: 目标文件路径
    """
    with open(path, 'wb') as f:
        f.write(_base64.b64decode(data.encode()))


# 导出
__all__ = [
    "encode",
    "decode",
    "encode_url_safe",
    "decode_url_safe",
    "encode_bytes",
    "decode_bytes",
    "encode_file",
    "decode_to_file",
]
