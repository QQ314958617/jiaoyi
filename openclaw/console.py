"""
Console - 控制台
基于 Claude Code console.ts 设计

控制台输出工具。
"""
import sys


class Console:
    """
    控制台
    """
    
    def __init__(self):
        self._stdout = sys.stdout
        self._stderr = sys.stderr
    
    def log(self, *args, **kwargs) -> None:
        """标准输出"""
        print(*args, **kwargs)
    
    def error(self, *args, **kwargs) -> None:
        """错误输出"""
        print(*args, file=self._stderr, **kwargs)
    
    def warn(self, *args, **kwargs) -> None:
        """警告输出"""
        print(*args, file=self._stderr, **kwargs)
    
    def info(self, *args, **kwargs) -> None:
        """信息输出"""
        print(*args, **kwargs)
    
    def debug(self, *args, **kwargs) -> None:
        """调试输出"""
        print(*args, **kwargs)
    
    def clear(self) -> None:
        """清屏"""
        print('\033[2J\033[H', end='')


def log(*args, **kwargs) -> None:
    print(*args, **kwargs)


def error(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


def warn(*args, **kwargs) -> None:
    print(*args, file=sys.stderr, **kwargs)


def info(*args, **kwargs) -> None:
    print(*args, **kwargs)


def debug(*args, **kwargs) -> None:
    print(*args, **kwargs)


# 导出
__all__ = [
    "Console",
    "log",
    "error",
    "warn",
    "info",
    "debug",
]
