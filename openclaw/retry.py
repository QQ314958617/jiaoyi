"""
Retry - 重试
基于 Claude Code retry.ts 设计

重试工具。
"""
import time
from typing import Callable, Optional


def retry(fn: Callable, attempts: int = 3, delay: float = 1.0, 
           backoff: float = 2.0, exceptions: tuple = (Exception,)) -> any:
    """
    重试装饰器/函数
    
    Args:
        fn: 要重试的函数
        attempts: 最大尝试次数
        delay: 初始延迟（秒）
        backoff: 退避倍数
        exceptions: 要捕获的异常类型
    """
    current_delay = delay
    
    for attempt in range(attempts):
        try:
            return fn()
        except exceptions as e:
            if attempt == attempts - 1:
                raise
            
            time.sleep(current_delay)
            current_delay *= backoff


def retry_async(fn: Callable, attempts: int = 3, delay: float = 1.0):
    """异步重试"""
    import asyncio
    
    async def wrapper():
        for attempt in range(attempts):
            try:
                return await fn()
            except Exception as e:
                if attempt == attempts - 1:
                    raise
                await asyncio.sleep(delay)
    
    return wrapper


class RetryError(Exception):
    """重试耗尽错误"""
    pass


class Retrier:
    """重试器"""
    
    def __init__(self, attempts: int = 3, delay: float = 1.0, 
                 backoff: float = 2.0, exceptions: tuple = (Exception,)):
        self.attempts = attempts
        self.delay = delay
        self.backoff = backoff
        self.exceptions = exceptions
    
    def run(self, fn: Callable) -> any:
        """运行函数并重试"""
        current_delay = self.delay
        
        for attempt in range(self.attempts):
            try:
                return fn()
            except self.exceptions as e:
                if attempt == self.attempts - 1:
                    raise RetryError(f"Failed after {self.attempts} attempts") from e
                
                time.sleep(current_delay)
                current_delay *= self.backoff
    
    def __call__(self, fn: Callable) -> Callable:
        """作为装饰器使用"""
        def wrapper(*args, **kwargs):
            return self.run(lambda: fn(*args, **kwargs))
        return wrapper


# 导出
__all__ = [
    "retry",
    "retry_async",
    "RetryError",
    "Retrier",
]
