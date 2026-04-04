"""
Screen - 屏幕
基于 Claude Code screen.ts 设计

屏幕工具。
"""
import shutil


def get_size() -> tuple:
    """获取终端大小 (cols, rows)"""
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def get_width() -> int:
    """获取终端宽度"""
    return shutil.get_terminal_size().columns


def get_height() -> int:
    """获取终端高度"""
    return shutil.get_terminal_size().lines


def clear():
    """清屏"""
    print('\033[2J\033[H', end='')


def clear_line():
    """清除当前行"""
    print('\033[2K', end='')


def cursor_hide():
    """隐藏光标"""
    print('\033[?25l', end='')


def cursor_show():
    """显示光标"""
    print('\033[?25h', end='')


def scroll_up(lines: int = 1):
    """向上滚动"""
    print(f'\033[{lines}S', end='')


def scroll_down(lines: int = 1):
    """向下滚动"""
    print(f'\033[{lines}T', end='')


class Screen:
    """屏幕"""
    
    @staticmethod
    def size() -> tuple:
        return get_size()
    
    @staticmethod
    def width() -> int:
        return get_width()
    
    @staticmethod
    def height() -> int:
        return get_height()
    
    @staticmethod
    def clear():
        clear()
    
    @staticmethod
    def clear_line():
        clear_line()


# 导出
__all__ = [
    "get_size",
    "get_width",
    "get_height",
    "clear",
    "clear_line",
    "cursor_hide",
    "cursor_show",
    "scroll_up",
    "scroll_down",
    "Screen",
]
