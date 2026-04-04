"""
GracefulShutdown - 优雅退出
基于 Claude Code graceful_shutdown.ts 设计

优雅退出工具。
"""
import signal
import sys
import atexit
from typing import Callable, List


class GracefulShutdown:
    """
    优雅关闭处理器
    """
    
    def __init__(self):
        self._handlers: List[Callable] = []
        self._cleanup: List[Callable] = []
        self._running = False
    
    def add_handler(self, handler: Callable):
        """
        添加关闭处理函数
        
        Args:
            handler: () -> None
        """
        self._handlers.append(handler)
    
    def add_cleanup(self, cleanup: Callable):
        """
        添加清理函数（atexit）
        """
        self._cleanup.append(cleanup)
    
    def register(self):
        """注册信号处理器"""
        self._running = True
        
        # 注册atexit
        atexit.register(self._do_cleanup)
        
        # 注册信号处理器
        def signal_handler(signum, frame):
            self._do_shutdown(signum)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _do_shutdown(self, signum: int):
        """处理信号"""
        print(f"\nReceived signal {signum}, shutting down...")
        for handler in self._handlers:
            try:
                handler()
            except Exception as e:
                print(f"Error in shutdown handler: {e}")
        self._running = False
        sys.exit(0)
    
    def _do_cleanup(self):
        """清理"""
        for cleanup in self._cleanup:
            try:
                cleanup()
            except Exception as e:
                print(f"Error in cleanup: {e}")
    
    def unregister(self):
        """取消注册"""
        self._running = False
        try:
            atexit.unregister(self._do_cleanup)
        except Exception:
            pass


# 全局实例
_shutdown_handler = GracefulShutdown()


def add_handler(handler: Callable):
    """添加全局关闭处理器"""
    _shutdown_handler.add_handler(handler)


def add_cleanup(cleanup: Callable):
    """添加全局清理函数"""
    _shutdown_handler.add_cleanup(cleanup)


def register():
    """注册全局处理器"""
    _shutdown_handler.register()


def shutdown():
    """执行关闭"""
    _shutdown_handler._do_shutdown(0)


# 导出
__all__ = [
    "GracefulShutdown",
    "add_handler",
    "add_cleanup",
    "register",
    "shutdown",
]
