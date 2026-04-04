"""
Resilience - 弹性模式
基于 Claude Code resilience.ts 设计

弹性设计模式。
"""
import asyncio
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')


class Bulkhead:
    """
    隔板模式
    
    限制并发数。
    """
    
    def __init__(self, max_concurrent: int = 10, max_queue: int = 100):
        """
        Args:
            max_concurrent: 最大并发数
            max_queue: 最大队列长度
        """
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._queue = asyncio.Queue(maxsize=max_queue)
        self._max_concurrent = max_concurrent
        self._max_queue = max_queue
    
    async def execute(self, func: Callable[[], T]) -> T:
        """执行函数"""
        async with self._semaphore:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()


class Timeout:
    """
    超时模式
    """
    
    def __init__(self, timeout_seconds: float):
        """
        Args:
            timeout_seconds: 超时秒数
        """
        self._timeout = timeout_seconds
    
    async def execute(self, coro) -> Any:
        """执行带超时的协程"""
        return await asyncio.wait_for(coro, timeout=self._timeout)


class CircuitBreaker2:
    """
    断路器2
    
    改进版断路器。
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
    ):
        """
        Args:
            failure_threshold: 失败阈值
            success_threshold: 成功阈值（半开->闭合）
            timeout_seconds: 尝试恢复的超时
        """
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._timeout = timeout_seconds
        
        self._state = "closed"  # closed, open, half-open
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
    
    async def execute(self, func: Callable[[], T]) -> T:
        """执行函数"""
        if self._state == "open":
            if (asyncio.get_event_loop().time() - self._last_failure_time >= 
                self._timeout):
                self._state = "half-open"
                self._success_count = 0
            else:
                raise RuntimeError("Circuit breaker is OPEN")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func()
            else:
                result = func()
            
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """成功处理"""
        if self._state == "half-open":
            self._success_count += 1
            if self._success_count >= self._success_threshold:
                self._state = "closed"
                self._failure_count = 0
        elif self._state == "closed":
            self._failure_count = max(0, self._failure_count - 1)
    
    def _on_failure(self) -> None:
        """失败处理"""
        self._failure_count += 1
        self._last_failure_time = asyncio.get_event_loop().time()
        
        if self._state == "half-open":
            self._state = "open"
        elif self._failure_count >= self._failure_threshold:
            self._state = "open"
    
    @property
    def state(self) -> str:
        """状态"""
        return self._state


def fallback(func: Callable, fallback_value: Any) -> Callable:
    """
    降级装饰器
    
    Args:
        func: 原函数
        fallback_value: 降级值
    """
    async def wrapper(*args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception:
            return fallback_value
    
    return wrapper


def circuit_breaker_decorator(
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout_seconds: float = 60.0,
):
    """
    断路器装饰器
    """
    breaker = CircuitBreaker2(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout_seconds=timeout_seconds,
    )
    
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            return await breaker.execute(lambda: func(*args, **kwargs))
        return wrapper
    
    return decorator


# 导出
__all__ = [
    "Bulkhead",
    "Timeout",
    "CircuitBreaker2",
    "fallback",
    "circuit_breaker_decorator",
]
