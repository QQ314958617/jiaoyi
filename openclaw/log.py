"""
Log - 日志
基于 Claude Code log.ts 设计

日志工具。
"""
import time
from enum import Enum
from typing import Any


class Level(Enum):
    """日志级别"""
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    NONE = 4


class Logger:
    """
    日志记录器
    """
    
    def __init__(self, name: str = "", level: Level = Level.INFO):
        """
        Args:
            name: 日志名
            level: 最小日志级别
        """
        self.name = name
        self.level = level
    
    def _format(self, level: Level, *args) -> str:
        """格式化日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[{timestamp}] [{level.name}]"
        if self.name:
            prefix += f" [{self.name}]"
        return prefix + " " + " ".join(str(a) for a in args)
    
    def debug(self, *args) -> None:
        """调试日志"""
        if self.level.value <= Level.DEBUG.value:
            print(self._format(Level.DEBUG, *args))
    
    def info(self, *args) -> None:
        """信息日志"""
        if self.level.value <= Level.INFO.value:
            print(self._format(Level.INFO, *args))
    
    def warn(self, *args) -> None:
        """警告日志"""
        if self.level.value <= Level.WARN.value:
            print(self._format(Level.WARN, *args))
    
    def error(self, *args) -> None:
        """错误日志"""
        if self.level.value <= Level.ERROR.value:
            import sys
            print(self._format(Level.ERROR, *args), file=sys.stderr)


# 全局日志器
_default_logger = Logger()


def get_logger(name: str = "", level: Level = Level.INFO) -> Logger:
    """
    获取日志器
    
    Args:
        name: 日志名
        level: 级别
        
    Returns:
        Logger实例
    """
    return Logger(name, level)


def debug(*args) -> None:
    _default_logger.debug(*args)


def info(*args) -> None:
    _default_logger.info(*args)


def warn(*args) -> None:
    _default_logger.warn(*args)


def error(*args) -> None:
    _default_logger.error(*args)


# 导出
__all__ = [
    "Level",
    "Logger",
    "get_logger",
    "debug",
    "info",
    "warn",
    "error",
]
