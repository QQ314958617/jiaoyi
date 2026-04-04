"""
Color - 颜色
基于 Claude Code color.ts 设计

颜色工具。
"""
from typing import Tuple


# ANSI颜色代码
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
    """RGB颜色"""
    return f'\033[38;2;{r};{g};{b}m'


def bg_rgb(r: int, g: int, b: int) -> str:
    """RGB背景色"""
    return f'\033[48;2;{r};{g};{b}m'


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """十六进制转RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB转十六进制"""
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def text(color: str, text: str) -> str:
    """彩色文本"""
    return f"{color}{text}{RESET}"


def red(text: str) -> str:
    """红色文本"""
    return f"{RED}{text}{RESET}"


def green(text: str) -> str:
    """绿色文本"""
    return f"{GREEN}{text}{RESET}"


def yellow(text: str) -> str:
    """黄色文本"""
    return f"{YELLOW}{text}{RESET}"


def blue(text: str) -> str:
    """蓝色文本"""
    return f"{BLUE}{text}{RESET}"


def cyan(text: str) -> str:
    """青色文本"""
    return f"{CYAN}{text}{RESET}"


def magenta(text: str) -> str:
    """品红文本"""
    return f"{MAGENTA}{text}{RESET}"


def is_dark(r: int, g: int, b: int) -> bool:
    """是否为深色"""
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance < 0.5


def is_light(r: int, g: int, b: int) -> bool:
    """是否为浅色"""
    return not is_dark(r, g, b)


# 导出
__all__ = [
    "RESET", "BOLD", "DIM",
    "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE",
    "rgb", "bg_rgb",
    "hex_to_rgb", "rgb_to_hex",
    "text",
    "red", "green", "yellow", "blue", "cyan", "magenta",
    "is_dark", "is_light",
]
