"""
Debounce - 防抖
基于 Claude Code debounce.ts 设计

防抖工具。
"""
import time
from typing import Callable, Optional


class Debouncer:
    """
    防抖器
    
    在指定时间内的多次调用只执行最后一次。
    """
    
    def __init__(self, wait: float, immediate: bool = False):
        """
        Args:
            wait: 等待时间（秒）
            immediate: 是否立即执行
        """
        self._wait = wait
        self._immediate = immediate
        self._timer: Optional[threading.Timer] = None
        self._last_time = 0
        self._result = None
    
    def __call__(self, fn: Callable, *args, **kwargs):
        """执行函数"""
        def wrapper():
            return fn(*args, **kwargs)
        
        if self._immediate:
            if self._timer is None:
                self._result = wrapper()
            self._cancel()
            self._timer = threading.Timer(self._wait, self._reset)
            self._timer.start()
            return self._result
        else:
            self._cancel()
            self._timer = threading.Timer(self._wait, wrapper)
            self._timer.start()
    
    def _cancel(self) -> None:
        """取消定时器"""
        if self._timer:
            self._timer.cancel()
            self._timer = None
    
    def _reset(self) -> None:
        """重置"""
        self._timer = None
    
    def cancel(self) -> None:
        """取消"""
        self._cancel()
    
    def flush(self) -> None:
        """立即执行并取消"""
        if self._timer:
            self._timer.cancel()
            self._timer = None


import threading


def debounce(wait: float, immediate: bool = False) -> Callable:
    """
    防抖装饰器
    
    Args:
        wait: 等待时间
        immediate: 是否立即执行
        
    Returns:
        装饰器
    """
    def decorator(fn: Callable) -> Callable:
        timer = [None]
        last_result = [None]
        
        def debounced(*args, **kwargs):
            def call():
                return fn(*args, **kwargs)
            
            if immediate:
                if timer[0] is None:
                    last_result[0] = call()
                if timer[0]:
                    timer[0].cancel()
                timer[0] = threading.Timer(wait, lambda: timer.__setitem__(0, None))
                timer[0].start()
            else:
                if timer[0]:
                    timer[0].cancel()
                timer[0] = threading.Timer(wait, call)
                timer[0].start()
            
            return last_result[0] if immediate else None
        
        debounced.cancel = lambda: timer[0] and timer[0].cancel()
        return debounced
    
    return decorator


# 导出
__all__ = [
    "Debouncer",
    "debounce",
]
