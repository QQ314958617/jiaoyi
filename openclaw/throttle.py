"""
Throttle - 节流
基于 Claude Code throttle.ts 设计

节流工具。
"""
import time
from typing import Callable


def throttle(fn: Callable, interval: float) -> Callable:
    """
    节流装饰器
    
    Args:
        fn: 要节流的函数
        interval: 最小间隔（秒）
    """
    last_call = [0.0]
    
    def throttled(*args, **kwargs):
        now = time.time()
        if now - last_call[0] >= interval:
            last_call[0] = now
            return fn(*args, **kwargs)
    
    return throttled


def debounce(fn: Callable, delay: float) -> Callable:
    """
    防抖装饰器
    
    Args:
        fn: 要防抖的函数
        delay: 延迟（秒）
    """
    timer = [None]
    
    def debounced(*args, **kwargs):
        if timer[0]:
            timer[0].cancel()
        
        def call_fn():
            fn(*args, **kwargs)
        
        import threading
        timer[0] = threading.Timer(delay, call_fn)
        timer[0].start()
    
    return debounced


def once(fn: Callable) -> Callable:
    """
    只执行一次
    """
    called = [False]
    result = [None]
    
    def wrapper(*args, **kwargs):
        if not called[0]:
            called[0] = True
            result[0] = fn(*args, **kwargs)
        return result[0]
    
    return wrapper


def after(times: int, fn: Callable) -> Callable:
    """
    执行times次后执行fn
    """
    counter = [0]
    
    def wrapper(*args, **kwargs):
        counter[0] += 1
        if counter[0] >= times:
            return fn(*args, **kwargs)
    
    return wrapper


class Throttler:
    """节流器"""
    
    def __init__(self, interval: float):
        self._interval = interval
        self._last_call = 0.0
    
    def should_proceed(self) -> bool:
        """是否应该继续"""
        now = time.time()
        if now - self._last_call >= self._interval:
            self._last_call = now
            return True
        return False
    
    def call(self, fn: Callable, *args, **kwargs):
        """调用函数"""
        if self.should_proceed():
            return fn(*args, **kwargs)


# 导出
__all__ = [
    "throttle",
    "debounce",
    "once",
    "after",
    "Throttler",
]
