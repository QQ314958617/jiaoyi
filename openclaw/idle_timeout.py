"""
IdleTimeout - 空闲超时
基于 Claude Code idle_timeout.ts 设计

空闲超时检测工具。
"""
import time
from typing import Callable, Optional


class IdleTimeout:
    """
    空闲超时检测器
    """
    
    def __init__(self, timeout: float, callback: Callable = None):
        """
        Args:
            timeout: 超时时间（秒）
            callback: 超时回调
        """
        self._timeout = timeout
        self._callback = callback
        self._last_activity = time.time()
        self._running = False
    
    def reset(self):
        """重置空闲时间"""
        self._last_activity = time.time()
    
    def check(self) -> bool:
        """
        检查是否超时
        
        Returns:
            是否超时
        """
        if time.time() - self._last_activity > self._timeout:
            if self._callback:
                self._callback()
            return True
        return False
    
    def start(self):
        """开始监控"""
        self._running = True
        self._last_activity = time.time()
    
    def stop(self):
        """停止监控"""
        self._running = False
    
    @property
    def idle_time(self) -> float:
        """空闲时间（秒）"""
        return time.time() - self._last_activity
    
    @property
    def is_idle(self) -> bool:
        """是否空闲"""
        return self.idle_time > self._timeout


def check(timeout: float, callback: Callable = None) -> bool:
    """
    检查空闲超时
    
    使用全局单例
    """
    global _idle_checker
    if '_idle_checker' not in globals():
        _idle_checker = IdleTimeout(timeout, callback)
        _idle_checker.start()
    return _idle_checker.check()


def reset():
    """重置全局空闲时间"""
    global _idle_checker
    if '_idle_checker' in globals():
        _idle_checker.reset()


# 导出
__all__ = [
    "IdleTimeout",
    "check",
    "reset",
]
