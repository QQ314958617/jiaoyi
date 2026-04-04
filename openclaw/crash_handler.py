"""
CrashHandler - 崩溃处理
基于 Claude Code crash_handler.ts 设计

崩溃处理工具。
"""
import sys
import traceback
import atexit
from typing import Callable, Optional


class CrashHandler:
    """
    崩溃处理器
    """
    
    def __init__(self):
        self._handlers: list = []
        self._registered = False
    
    def add_handler(self, handler: Callable[[Exception], None]):
        """添加崩溃处理函数"""
        self._handlers.append(handler)
    
    def handle(self, exc: Exception):
        """处理异常"""
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_str = ''.join(tb)
        
        for handler in self._handlers:
            try:
                handler(exc)
            except Exception as e:
                print(f"Error in crash handler: {e}", file=sys.stderr)
        
        return tb_str
    
    def register(self):
        """注册全局处理器"""
        if self._registered:
            return
        
        self._registered = True
        
        def exception_handler(exc_type, exc_value, exc_traceback):
            """全局异常处理器"""
            if issubclass(exc_type, KeyboardInterrupt):
                # 不处理Ctrl+C
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            exc = Exception(str(exc_type.__name__))
            tb_str = self.handle(exc)
            
            print(f"Fatal error: {exc}", file=sys.stderr)
            print(tb_str, file=sys.stderr)
            
            sys.exit(1)
        
        sys.excepthook = exception_handler
        
        # atexit清理
        atexit.register(self._cleanup)
    
    def _cleanup(self):
        """清理"""
        pass


# 全局实例
_handler = CrashHandler()


def add_handler(handler: Callable):
    """添加全局处理函数"""
    _handler.add_handler(handler)


def register():
    """注册全局处理器"""
    _handler.register()


def handle(exc: Exception):
    """处理异常"""
    return _handler.handle(exc)


# 导出
__all__ = [
    "CrashHandler",
    "add_handler",
    "register",
    "handle",
]
