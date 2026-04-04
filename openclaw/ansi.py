"""
Ansi - ANSI转义序列
基于 Claude Code ansi.ts 设计

ANSI转义序列工具。
"""


# 控制码
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
ITALIC = '\033[3m'
UNDERLINE = '\033[4m'
BLINK = '\033[5m'
REVERSE = '\033[7m'
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

# 亮色前景
BRIGHT_BLACK = '\033[90m'
BRIGHT_RED = '\033[91m'
BRIGHT_GREEN = '\033[92m'
BRIGHT_YELLOW = '\033[93m'
BRIGHT_BLUE = '\033[94m'
BRIGHT_MAGENTA = '\033[95m'
BRIGHT_CYAN = '\033[96m'
BRIGHT_WHITE = '\033[97m'

# 亮色背景
BG_BRIGHT_BLACK = '\033[100m'
BG_BRIGHT_RED = '\033[101m'
BG_BRIGHT_GREEN = '\033[102m'
BG_BRIGHT_YELLOW = '\033[103m'
BG_BRIGHT_BLUE = '\033[104m'
BG_BRIGHT_MAGENTA = '\033[105m'
BG_BRIGHT_CYAN = '\033[106m'
BG_BRIGHT_WHITE = '\033[107m'


def rgb(r: int, g: int, b: int) -> str:
    """256色RGB"""
    return f'\033[38;2;{r};{g};{b}m'


def bg_rgb(r: int, g: int, b: int) -> str:
    """RGB背景"""
    return f'\033[48;2;{r};{g};{b}m'


def cursor_up(n: int = 1) -> str:
    """光标上移"""
    return f'\033[{n}A'


def cursor_down(n: int = 1) -> str:
    """光标下移"""
    return f'\033[{n}B'


def cursor_right(n: int = 1) -> str:
    """光标右移"""
    return f'\033[{n}C'


def cursor_left(n: int = 1) -> str:
    """光标左移"""
    return f'\033[{n}D'


def cursor_move(x: int, y: int) -> str:
    """光标移动到(x,y)"""
    return f'\033[{y};{x}H'


def cursor_save() -> str:
    """保存光标位置"""
    return '\033[s'


def cursor_restore() -> str:
    """恢复光标位置"""
    return '\033[u'


def cursor_clear() -> str:
    """清除屏幕"""
    return '\033[2J'


def clear_line() -> str:
    """清除当前行"""
    return '\033[2K'


def clear_line_right() -> str:
    """清除到行尾"""
    return '\033[0K'


def clear_line_left() -> str:
    """清除到行首"""
    return '\033[1K'


def hide_cursor() -> str:
    """隐藏光标"""
    return '\033[?25l'


def show_cursor() -> str:
    """显示光标"""
    return '\033[?25h'


def screen_save() -> str:
    """保存屏幕"""
    return '\033[?47h'


def screen_restore() -> str:
    """恢复屏幕"""
    return '\033[?47l'


# 导出
__all__ = [
    "RESET", "BOLD", "DIM", "ITALIC", "UNDERLINE",
    "BLINK", "REVERSE", "HIDDEN", "STRIKETHROUGH",
    "BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE",
    "BG_BLACK", "BG_RED", "BG_GREEN", "BG_YELLOW", "BG_BLUE", "BG_MAGENTA", "BG_CYAN", "BG_WHITE",
    "BRIGHT_BLACK", "BRIGHT_RED", "BRIGHT_GREEN", "BRIGHT_YELLOW", "BRIGHT_BLUE", "BRIGHT_MAGENTA", "BRIGHT_CYAN", "BRIGHT_WHITE",
    "BG_BRIGHT_BLACK", "BG_BRIGHT_RED", "BG_BRIGHT_GREEN", "BG_BRIGHT_YELLOW", "BG_BRIGHT_BLUE", "BG_BRIGHT_MAGENTA", "BG_BRIGHT_CYAN", "BG_BRIGHT_WHITE",
    "rgb", "bg_rgb",
    "cursor_up", "cursor_down", "cursor_right", "cursor_left", "cursor_move",
    "cursor_save", "cursor_restore", "cursor_clear", "clear_line",
    "clear_line_right", "clear_line_left",
    "hide_cursor", "show_cursor",
    "screen_save", "screen_restore",
]
