"""
Color - 颜色
基于 Claude Code color.ts 设计

颜色工具。
"""
from typing import Tuple


# 颜色代码
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
WHITE = '\033[97m'


def rgb(r: int, g: int, b: int) -> str:
    """
    RGB颜色
    
    Args:
        r, g, b: 0-255
        
    Returns:
        ANSI颜色代码
    """
    return f'\033[38;2;{r};{g};{b}m'


def bg_rgb(r: int, g: int, b: int) -> str:
    """
    RGB背景色
    
    Args:
        r, g, b: 0-255
        
    Returns:
        ANSI颜色代码
    """
    return f'\033[48;2;{r};{g};{b}m'


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    十六进制转RGB
    
    Args:
        hex_color: 十六进制颜色 (#RRGGBB)
        
    Returns:
        (r, g, b)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    RGB转十六进制
    
    Args:
        r, g, b: 0-255
        
    Returns:
        十六进制颜色
    """
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def text(color: str, text: str) -> str:
    """
    彩色文本
    
    Args:
        color: 颜色代码
        text: 文本
        
    Returns:
        带颜色的文本
    """
    return f"{color}{text}{RESET}"


def bold_text(text: str) -> str:
    """粗体文本"""
    return f"{BOLD}{text}{RESET}"


def red(text: str) -> str:
    """红色文本"""
    return text(RED, text)


def green(text: str) -> str:
    """绿色文本"""
    return text(GREEN, text)


def yellow(text: str) -> str:
    """黄色文本"""
    return text(YELLOW, text)


def blue(text: str) -> str:
    """蓝色文本"""
    return text(BLUE, text)


def cyan(text: str) -> str:
    """青色文本"""
    return text(CYAN, text)


def magenta(text: str) -> str:
    """品红文本"""
    return text(MAGENTA, text)


def is_dark(r: int, g: int, b: int) -> bool:
    """是否为深色"""
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance < 0.5


# 导出
__all__ = [
    "RESET", "BOLD", "DIM",
    "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE",
    "rgb", "bg_rgb",
    "hex_to_rgb", "rgb_to_hex",
    "text", "bold_text",
    "red", "green", "yellow", "blue", "cyan", "magenta",
    "is_dark",
]
