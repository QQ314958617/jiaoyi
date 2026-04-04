"""
Debounce - 防抖
基于 Claude Code debounce.ts 设计

防抖和节流装饰器。
"""
import asyncio
import time
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar('T')


def debounce(wait_ms: int):
    """
    防抖装饰器
    
    Args:
        wait_ms: 等待毫秒数
        
    Returns:
        装饰器
    """
    def decorator(func: Callable) -> Callable:
        last_call = [0]
        timer = [None]
        
        @wraps(func)
        def debounced(*args, **kwargs):
            def call_it():
                last_call[0] = time.time()
                return func(*args, **kwargs)
            
            now = time.time()
            remaining = wait_ms / 1000 - (now - last_call[0])
            
            if timer[0]:
                timer[0].cancel()
            
            if remaining <= 0:
                timer[0] = None
                return call_it()
            else:
                timer[0] = threading.Timer(remaining, call_it)
                timer[0].start()
        
        return debounced
    return decorator


def throttle(wait_ms: int):
    """
    节流装饰器
    
    Args:
        wait_ms: 间隔毫秒数
        
    Returns:
        装饰器
    """
    def decorator(func: Callable) -> Callable:
        last_call = [0]
        timer = [None]
        
        @wraps(func)
        def throttled(*args, **kwargs):
            now = time.time()
            
            if now - last_call[0] >= wait_ms / 1000:
                last_call[0] = now
                return func(*args, **kwargs)
            else:
                # 记录最后一次调用
                def delayed():
                    last_call[0] = time.time()
                    func(*args, **kwargs)
                
                if not timer[0]:
                    timer[0] = threading.Timer(
                        (wait_ms / 1000) - (now - last_call[0]),
                        delayed
                    )
                    timer[0].start()
        
        return throttled
    return decorator


import threading


class Debouncer:
    """
    防抖类
    
    手动控制防抖。
    """
    
    def __init__(self, wait_ms: int):
        self._wait_ms = wait_ms
        self._timer: threading.Timer = None
    
    def call(self, func: Callable, *args, **kwargs) -> None:
        """调用"""
        if self._timer:
            self._timer.cancel()
        
        def execute():
            func(*args, **kwargs)
        
        self._timer = threading.Timer(self._wait_ms / 1000, execute)
        self._timer.start()
    
    def cancel(self) -> None:
        """取消"""
        if self._timer:
            self._timer.cancel()
            self._timer = None


# 异步版本
def async_debounce(wait_ms: int):
    """异步防抖"""
    def decorator(func: Callable) -> Callable:
        timer = [None]
        
        @wraps(func)
        async def debounced(*args, **kwargs):
            async def call_it():
                await func(*args, **kwargs)
            
            if timer[0]:
                timer[0].cancel()
            
            loop = asyncio.get_event_loop()
            timer[0] = loop.call_later(wait_ms / 1000, lambda: asyncio.create_task(call_it()))
        
        return debounced
    return decorator


def async_throttle(wait_ms: int):
    """异步节流"""
    def decorator(func: Callable) -> Callable:
        last_call = [0]
        timer = [None]
        
        @wraps(func)
        async def throttled(*args, **kwargs):
            now = time.time()
            
            if now - last_call[0] >= wait_ms / 1000:
                last_call[0] = now
                return await func(*args, **kwargs)
            else:
                async def delayed():
                    last_call[0] = time.time()
                    await func(*args, **kwargs)
                
                if not timer[0]:
                    loop = asyncio.get_event_loop()
                    timer[0] = loop.call_later(
                        (wait_ms / 1000) - (now - last_call[0]),
                        lambda: asyncio.create_task(delayed())
                    )
        
        return throttled
    return decorator


# 导出
__all__ = [
    "debounce",
    "throttle",
    "Debouncer",
    "async_debounce",
    "async_throttle",
]
