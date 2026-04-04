"""
Once - 单次执行保证
基于 Claude Code once.ts 设计

确保函数只执行一次。
"""
import threading
from typing import Callable, TypeVar

T = TypeVar('T')


class Once:
    """
    保证函数只执行一次
    
    第一次调用会执行函数，后续调用返回第一次的结果。
    """
    
    def __init__(self):
        self._done = False
        self._result = None
        self._error = None
        self._lock = threading.Lock()
    
    def call(self, fn: Callable[[], T]) -> T:
        """
        调用函数（如果尚未调用）
        
        Args:
            fn: 要执行的函数
            
        Returns:
            函数结果
        """
        with self._lock:
            if self._done:
                if self._error is not None:
                    raise self._error
                return self._result
            
            try:
                self._result = fn()
                self._done = True
                return self._result
            except Exception as e:
                self._error = e
                self._done = True
                raise


def once(fn: Callable[[], T]) -> Callable[[], T]:
    """
    装饰器：确保函数只执行一次
    
    Args:
        fn: 要包装的函数
        
    Returns:
        包装后的函数
    """
    once_guard = Once()
    
    def wrapper() -> T:
        return once_guard.call(fn)
    
    return wrapper


class OnceAsync:
    """
    异步版本的Once
    """
    
    def __init__(self):
        self._done = False
        self._result = None
        self._error = None
        self._lock = threading.Lock()
    
    async def call(self, fn: Callable) -> T:
        """
        调用异步函数（如果尚未调用）
        
        Args:
            fn: 要执行的异步函数
            
        Returns:
            函数结果
        """
        with self._lock:
            if self._done:
                if self._error is not None:
                    raise self._error
                return self._result
            
            try:
                import asyncio
                if asyncio.iscoroutinefunction(fn):
                    self._result = await fn()
                else:
                    self._result = fn()
                self._done = True
                return self._result
            except Exception as e:
                self._error = e
                self._done = True
                raise


async def once_async(fn: Callable) -> Callable:
    """
    装饰器：确保异步函数只执行一次
    
    Args:
        fn: 要包装的异步函数
        
    Returns:
        包装后的函数
    """
    once_guard = OnceAsync()
    
    async def wrapper() -> T:
        return await once_guard.call(fn)
    
    return wrapper


# 导出
__all__ = [
    "Once",
    "once",
    "OnceAsync",
    "once_async",
]
