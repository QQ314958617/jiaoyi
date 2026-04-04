"""
Ansi - ANSI转义码
基于 Claude Code ansi.ts 设计

ANSI转义码工具。
"""


# 重置
RESET = '\033[0m'

# 样式
BOLD = '\033[1m'
DIM = '\033[2m'
ITALIC = '\033[3m'
UNDERLINE = '\033[4m'
INVERSE = '\033[7m'
HIDDEN = '\033[8m'
STRIKETHROUGH = '\033[9m'

# 前景色
BLACK = '\033[30m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
WHITE = '\033[37m'

# 背景色
BG_BLACK = '\033[40m'
BG_RED = '\033[41m'
BG_GREEN = '\033[42m'
BG_YELLOW = '\033[43m'
BG_BLUE = '\033[44m'
BG_MAGENTA = '\033[45m'
BG_CYAN = '\033[46m'
BG_WHITE = '\033[47m'


def styled(text: str, *styles: str) -> str:
    """应用样式"""
    return ''.join(styles) + text + RESET


def bold(text: str) -> str:
    return BOLD + text + RESET


def dim(text: str) -> str:
    return DIM + text + RESET


def italic(text: str) -> str:
    return ITALIC + text + RESET


def underline(text: str) -> str:
    return UNDERLINE + text + RESET


def red(text: str) -> str:
    return RED + text + RESET


def green(text: str) -> str:
    return GREEN + text + RESET


def yellow(text: str) -> str:
    return YELLOW + text + RESET


def blue(text: str) -> str:
    return BLUE + text + RESET


def cyan(text: str) -> str:
    return CYAN + text + RESET


def magenta(text: str) -> str:
    return MAGENTA + text + RESET


def rgb(r: int, g: int, b: int) -> str:
    """RGB前景色"""
    return f'\033[38;2;{r};{g};{b}m'


def bg_rgb(r: int, g: int, b: int) -> str:
    """RGB背景色"""
    return f'\033[48;2;{r};{g};{b}m'


def cursor_to(x: int, y: int) -> str:
    """移动光标到位置"""
    return f'\033[{y};{x}H'


def cursor_up(n: int = 1) -> str:
    """上移光标"""
    return f'\033[{n}A'


def cursor_down(n: int = 1) -> str:
    """下移光标"""
    return f'\033[{n}B'


def cursor_right(n: int = 1) -> str:
    """右移光标"""
    return f'\033[{n}C'


def cursor_left(n: int = 1) -> str:
    """左移光标"""
    return f'\033[{n}D'


def clear_screen() -> str:
    """清屏"""
    return '\033[2J'


def clear_line() -> str:
    """清除当前行"""
    return '\033[2K'


# 导出
__all__ = [
    "RESET",
    "BOLD", "DIM", "ITALIC", "UNDERLINE", "INVERSE", "HIDDEN", "STRIKETHROUGH",
    "BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE",
    "BG_BLACK", "BG_RED", "BG_GREEN", "BG_YELLOW", "BG_BLUE", "BG_MAGENTA", "BG_CYAN", "BG_WHITE",
    "styled",
    "bold", "dim", "italic", "underline",
    "red", "green", "yellow", "blue", "cyan", "magenta",
    "rgb", "bg_rgb",
    "cursor_to", "cursor_up", "cursor_down", "cursor_right", "cursor_left",
    "clear_screen", "clear_line",
]
