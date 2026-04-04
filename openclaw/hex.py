"""
Hex - 十六进制
基于 Claude Code hex.ts 设计

十六进制工具。
"""
from typing import Union


def encode(data: bytes) -> str:
    """
    编码为十六进制字符串
    
    Args:
        data: 字节数据
        
    Returns:
        十六进制字符串
    """
    return data.hex()


def decode(hex_str: str) -> bytes:
    """
    从十六进制字符串解码
    
    Args:
        hex_str: 十六进制字符串
        
    Returns:
        字节数据
    """
    return bytes.fromhex(hex_str)


def is_hex(text: str) -> bool:
    """
    检查是否为有效的十六进制字符串
    
    Args:
        text: 文本
        
    Returns:
        是否为十六进制
    """
    try:
        bytes.fromhex(text)
        return True
    except ValueError:
        return False


def to_int(hex_str: str) -> int:
    """
    十六进制字符串转整数
    
    Args:
        hex_str: 十六进制字符串
        
    Returns:
        整数
    """
    return int(hex_str, 16)


def from_int(value: int, length: int = None) -> str:
    """
    整数转十六进制字符串
    
    Args:
        value: 整数
        length: 最小长度
        
    Returns:
        十六进制字符串
    """
    hex_str = format(value, 'x')
    if length and len(hex_str) < length:
        hex_str = hex_str.zfill(length)
    return hex_str


def to_rgb(hex_color: str) -> tuple:
    """
    十六进制颜色转RGB
    
    Args:
        hex_color: 十六进制颜色 (#RRGGBB)
        
    Returns:
        (r, g, b) 元组
    """
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def from_rgb(r: int, g: int, b: int) -> str:
    """
    RGB转十六进制颜色
    
    Args:
        r, g, b: 0-255
        
    Returns:
        #RRGGBB
    """
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


# 导出
__all__ = [
    "encode",
    "decode",
    "is_hex",
    "to_int",
    "from_int",
    "to_rgb",
    "from_rgb",
]
