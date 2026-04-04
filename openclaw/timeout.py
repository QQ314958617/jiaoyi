"""
Timeout - 超时工具
基于 Claude Code timeout.ts 设计

超时控制工具。
"""
import asyncio
import functools
from typing import Callable, Optional, TypeVar

T = TypeVar('T')


class TimeoutError(Exception):
    """超时错误"""
    pass


async def with_timeout(
    coro,
    timeout_ms: int,
    error_message: str = "Operation timed out",
) -> any:
    """
    带超时的协程执行
    
    Args:
        coro: 协程
        timeout_ms: 超时毫秒
        error_message: 错误消息
        
    Returns:
        协程结果
        
    Raises:
        TimeoutError: 超时
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_ms / 1000)
    except asyncio.TimeoutError:
        raise TimeoutError(error_message)


def timeout_ms(ms: int) -> Callable:
    """
    超时装饰器
    
    Args:
        ms: 超时毫秒
        
    Returns:
        装饰器
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await with_timeout(
                func(*args, **kwargs),
                ms,
                f"{func.__name__} timed out after {ms}ms"
            )
        return wrapper
    return decorator


def with_timeout_sync(
    func: Callable,
    timeout_ms: int,
    *args,
    **kwargs
) -> any:
    """
    带超时的同步函数执行
    
    Args:
        func: 函数
        timeout_ms: 超时毫秒
        *args, **kwargs: 函数参数
        
    Returns:
        函数结果
        
    Raises:
        TimeoutError: 超时
    """
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_ms / 1000)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Operation timed out after {timeout_ms}ms")


# 导出
__all__ = [
    "TimeoutError",
    "with_timeout",
    "timeout_ms",
    "with_timeout_sync",
]
