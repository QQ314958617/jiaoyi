"""
Retry2 - 重试
基于 Claude Code retry.ts 设计

重试工具。
"""
import time
from typing import Callable, Optional, Type, Tuple


def retry(
    fn: Callable,
    times: int = 3,
    delay: float = 0,
    backoff: float = 1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> any:
    """
    重试函数
    
    Args:
        fn: 要执行的函数
        times: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍增
        exceptions: 需要重试的异常类型
        
    Returns:
        函数返回值
        
    Raises:
        最后一次执行的异常
    """
    last_error = None
    current_delay = delay
    
    for i in range(times):
        try:
            return fn()
        except exceptions as e:
            last_error = e
            if i < times - 1:
                time.sleep(current_delay)
                current_delay *= backoff
    
    raise last_error


def retry_async(
    fn: Callable,
    times: int = 3,
    delay: float = 0,
    backoff: float = 1,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    异步重试
    
    Args:
        fn: 异步函数
        times: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍增
        exceptions: 需要重试的异常类型
    """
    import asyncio
    
    async def wrapper():
        last_error = None
        current_delay = delay
        
        for i in range(times):
            try:
                return await fn()
            except exceptions as e:
                last_error = e
                if i < times - 1:
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        raise last_error
    
    return wrapper()


class RetryContext:
    """重试上下文"""
    
    def __init__(self, times: int = 3, delay: float = 0):
        self.times = times
        self.delay = delay
        self.attempt = 0
        self.last_error = None
    
    def should_retry(self) -> bool:
        """是否应该重试"""
        return self.attempt < self.times
    
    def record_failure(self, error: Exception) -> None:
        """记录失败"""
        self.attempt += 1
        self.last_error = error
    
    def record_success(self) -> None:
        """记录成功"""
        pass


def exponential_backoff(attempt: int, base: float = 1, max_delay: float = 60) -> float:
    """
    指数退避
    
    Args:
        attempt: 第几次尝试
        base: 基础延迟（秒）
        max_delay: 最大延迟
        
    Returns:
        延迟时间
    """
    delay = min(base * (2 ** attempt), max_delay)
    return delay


def jitter(delay: float, amount: float = 0.1) -> float:
    """
    添加抖动
    
    Args:
        delay: 基础延迟
        amount: 抖动量（比例）
        
    Returns:
        带抖动的延迟
    """
    import random
    return delay * (1 + random.uniform(-amount, amount))


# 导出
__all__ = [
    "retry",
    "retry_async",
    "RetryContext",
    "exponential_backoff",
    "jitter",
]
