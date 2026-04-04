"""
Retry - 重试工具
基于 Claude Code retry.ts 设计

带重试逻辑的工具。
"""
import asyncio
import functools
import random
from typing import Callable, Optional, TypeVar

T = TypeVar('T')


class RetryError(Exception):
    """重试耗尽错误"""
    def __init__(self, attempts: int, last_error: Exception):
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"Failed after {attempts} attempts: {last_error}")


async def retry_async(
    coro_func: Callable,
    *args,
    max_attempts: int = 3,
    initial_delay_ms: int = 100,
    max_delay_ms: int = 5000,
    backoff_multiplier: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
    **kwargs
) -> any:
    """
    异步函数重试
    
    Args:
        coro_func: 异步函数
        *args: 函数参数
        max_attempts: 最大尝试次数
        initial_delay_ms: 初始延迟
        max_delay_ms: 最大延迟
        backoff_multiplier: 退避乘数
        jitter: 是否添加抖动
        exceptions: 需要重试的异常类型
        **kwargs: 函数关键字参数
        
    Returns:
        函数结果
        
    Raises:
        RetryError: 重试耗尽
    """
    last_error = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_func(*args, **kwargs)
        except exceptions as e:
            last_error = e
            
            if attempt == max_attempts:
                break
            
            # 计算延迟
            delay = min(
                initial_delay_ms * (backoff_multiplier ** (attempt - 1)),
                max_delay_ms
            )
            
            # 添加抖动
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            
            await asyncio.sleep(delay / 1000)
    
    raise RetryError(max_attempts, last_error)


def retry(
    func: Callable,
    *args,
    max_attempts: int = 3,
    initial_delay_ms: int = 100,
    max_delay_ms: int = 5000,
    backoff_multiplier: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
    **kwargs
) -> any:
    """
    同步函数重试
    
    Args:
        func: 函数
        *args: 函数参数
        max_attempts: 最大尝试次数
        initial_delay_ms: 初始延迟
        max_delay_ms: 最大延迟
        backoff_multiplier: 退避乘数
        jitter: 是否添加抖动
        exceptions: 需要重试的异常类型
        **kwargs: 函数关键字参数
        
    Returns:
        函数结果
        
    Raises:
        RetryError: 重试耗尽
    """
    import time
    
    last_error = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_error = e
            
            if attempt == max_attempts:
                break
            
            # 计算延迟
            delay = min(
                initial_delay_ms * (backoff_multiplier ** (attempt - 1)),
                max_delay_ms
            )
            
            # 添加抖动
            if jitter:
                delay = delay * (0.5 + random.random() * 0.5)
            
            time.sleep(delay / 1000)
    
    raise RetryError(max_attempts, last_error)


def retry_decorator(
    max_attempts: int = 3,
    initial_delay_ms: int = 100,
    max_delay_ms: int = 5000,
    backoff_multiplier: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        initial_delay_ms: 初始延迟
        max_delay_ms: 最大延迟
        backoff_multiplier: 退避乘数
        jitter: 是否添加抖动
        exceptions: 需要重试的异常类型
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_async(
                func, *args,
                max_attempts=max_attempts,
                initial_delay_ms=initial_delay_ms,
                max_delay_ms=max_delay_ms,
                backoff_multiplier=backoff_multiplier,
                jitter=jitter,
                exceptions=exceptions,
                **kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return retry(
                func, *args,
                max_attempts=max_attempts,
                initial_delay_ms=initial_delay_ms,
                max_delay_ms=max_delay_ms,
                backoff_multiplier=backoff_multiplier,
                jitter=jitter,
                exceptions=exceptions,
                **kwargs
            )
        
        # 根据函数类型返回正确的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# 导出
__all__ = [
    "RetryError",
    "retry_async",
    "retry",
    "retry_decorator",
]
