"""
AsyncUtils2 - 异步工具2
基于 Claude Code asyncUtils2.ts 设计

额外的异步工具。
"""
import asyncio
from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar('T')


async def retry_async(
    func: Callable,
    max_attempts: int = 3,
    delay_ms: int = 1000,
    backoff: float = 2.0,
) -> Any:
    """
    异步重试
    
    Args:
        func: 要重试的函数
        max_attempts: 最大尝试次数
        delay_ms: 初始延迟毫秒
        backoff: 退避倍数
        
    Returns:
        函数结果
    """
    delay = delay_ms / 1000
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            await asyncio.sleep(delay)
            delay *= backoff


async def timeout_async(coro, timeout_seconds: float) -> Any:
    """
    异步超时
    
    Args:
        coro: 协程
        timeout_seconds: 超时秒数
        
    Returns:
        协程结果
        
    Raises:
        asyncio.TimeoutError: 超时时
    """
    return await asyncio.wait_for(coro, timeout=timeout_seconds)


async def gather_with_concurrency(n: int, *coros) -> list:
    """
    并发限制的gather
    
    Args:
        n: 最大并发数
        *coros: 协程列表
        
    Returns:
        结果列表
    """
    semaphore = asyncio.Semaphore(n)
    
    async def run(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*(run(c) for c in coros))


async def race_async(*coros) -> Any:
    """
    竞速（返回最先完成的）
    
    Args:
        *coros: 协程列表
        
    Returns:
        最先完成的结果
    """
    done, pending = await asyncio.wait(
        [asyncio.create_task(c) for c in coros],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    for task in pending:
        task.cancel()
    
    return done.pop().result()


async def sleep_ms(ms: int) -> None:
    """
    毫秒级睡眠
    
    Args:
        ms: 毫秒数
    """
    await asyncio.sleep(ms / 1000)


class AsyncBatch:
    """
    异步批处理
    
    批量处理请求。
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        max_wait_ms: int = 100,
    ):
        """
        Args:
            batch_size: 批大小
            max_wait_ms: 最大等待毫秒
        """
        self._batch_size = batch_size
        self._max_wait_ms = max_wait_ms
        self._queue: list = []
        self._futures: list = []
        self._lock = asyncio.Lock()
        self._timer: Optional[asyncio.Task] = None
    
    async def add(self, item) -> list:
        """添加项并等待批处理"""
        future = asyncio.Future()
        
        async with self._lock:
            self._queue.append((item, future))
            
            if len(self._queue) >= self._batch_size:
                await self._flush()
            elif not self._timer:
                self._timer = asyncio.create_task(self._wait_and_flush())
        
        return await future
    
    async def _wait_and_flush(self) -> None:
        """等待后刷新"""
        await asyncio.sleep(self._max_wait_ms / 1000)
        async with self._lock:
            await self._flush()
    
    async def _flush(self) -> None:
        """刷新队列"""
        if self._timer:
            self._timer.cancel()
            self._timer = None
        
        if not self._queue:
            return
        
        items = self._queue.copy()
        futures = [f for _, f in items]
        self._queue.clear()
        
        # 这里应该调用实际的处理函数
        # 简化版本直接完成所有future
        results = items
        for (_, future), result in zip(items, results):
            future.set_result(result)


# 导出
__all__ = [
    "retry_async",
    "timeout_async",
    "gather_with_concurrency",
    "race_async",
    "sleep_ms",
    "AsyncBatch",
]
