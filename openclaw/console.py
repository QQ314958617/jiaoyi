"""
Console - 控制台
基于 Claude Code console.ts 设计

控制台工具。
"""
import sys


def log(*args, **kwargs):
    """标准输出"""
    print(*args, **kwargs)


def error(*args, **kwargs):
    """错误输出"""
    print(*args, file=sys.stderr, **kwargs)


def info(*args, **kwargs):
    """信息输出"""
    print(*args, **kwargs)


def warn(*args, **kwargs):
    """警告输出"""
    print(*args, file=sys.stderr, **kwargs)


def debug(*args, **kwargs):
    """调试输出"""
    import os
    if os.getenv('DEBUG'):
        print(*args, **kwargs)


def clear():
    """清屏"""
    print('\033[2J\033[H', end='')


class Console:
    """控制台类"""
    
    def log(self, *args, **kwargs):
        log(*args, **kwargs)
    
    def error(self, *args, **kwargs):
        error(*args, **kwargs)
    
    def info(self, *args, **kwargs):
        info(*args, **kwargs)
    
    def warn(self, *args, **kwargs):
        warn(*args, **kwargs)


# 导出
__all__ = [
    "log",
    "error",
    "info",
    "warn",
    "debug",
    "clear",
    "Console",
]
