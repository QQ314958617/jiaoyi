"""
WarningHandler - 警告处理
基于 Claude Code warning_handler.ts 设计

警告处理工具。
"""
import warnings
import sys
from typing import Callable, List, Optional


class WarningHandler:
    """
    警告处理器
    """
    
    def __init__(self):
        self._handlers: List[Callable] = []
        self._enabled = True
    
    def add_handler(self, handler: Callable):
        """
        添加警告处理函数
        
        Args:
            handler: (message, category, filename, lineno) -> None
        """
        self._handlers.append(handler)
    
    def handle(self, message: str, category: type, filename: str, lineno: int):
        """处理警告"""
        if self._enabled:
            for handler in self._handlers:
                handler(message, category, filename, lineno)
    
    def enable(self):
        """启用"""
        self._enabled = True
    
    def disable(self):
        """禁用"""
        self._enabled = False


# 全局实例
_warning_handler = WarningHandler()


def add_handler(handler: Callable):
    """添加全局处理器"""
    _warning_handler.add_handler(handler)


def emit(message: str, category: type = UserWarning):
    """发出警告"""
    _warning_handler.handle(message, category, "", 0)


def simple_handler(message: str, category: type, filename: str, lineno: int):
    """简单处理器：打印到stderr"""
    print(f"Warning: {message}", file=sys.stderr)


# 默认添加简单处理器
_warning_handler.add_handler(simple_handler)


# 集成Python warnings模块
def setup_warnings():
    """设置warnings模块集成"""
    warnings.showwarning = lambda message, category, filename, lineno: \
        _warning_handler.handle(str(message), category, filename, lineno)


# 导出
__all__ = [
    "WarningHandler",
    "add_handler",
    "emit",
    "setup_warnings",
]
