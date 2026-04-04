"""
Async Utilities - 异步工具
基于 Claude Code async.ts 设计

常用的异步操作工具。
"""
import asyncio
from typing import Any, Callable, Coroutine, List, Optional, TypeVar

T = TypeVar('T')


async def sleep(ms: int) -> None:
    """
    异步睡眠
    
    Args:
        ms: 毫秒数
    """
    await asyncio.sleep(ms / 1000)


async def wait_for(
    coro: Coroutine,
    timeout_ms: Optional[int] = None,
) -> Any:
    """
    等待协程完成，带超时
    
    Args:
        coro: 协程
        timeout_ms: 超时毫秒
        
    Returns:
        协程结果
        
    Raises:
        asyncio.TimeoutError: 超时
    """
    if timeout_ms is None:
        return await coro
    
    try:
        return await asyncio.wait_for(coro, timeout=timeout_ms / 1000)
    except asyncio.TimeoutError:
        raise


async def gather_with_concurrency(
    max_concurrent: int,
    *coros: Coroutine,
) -> List[Any]:
    """
    控制并发数的gather
    
    Args:
        max_concurrent: 最大并发数
        *coros: 协程列表
        
    Returns:
        结果列表
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_coro(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*[bounded_coro(c) for c in coros])


def run_sync(coro: Coroutine) -> Any:
    """
    在同步上下文中运行协程
    
    Args:
        coro: 协程
        
    Returns:
        协程结果
    """
    try:
        loop = asyncio.get_running_loop()
        # 在已有循环中创建task
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # 没有运行中的循环
        return asyncio.run(coro)


class AsyncBatch:
    """
    异步批处理器
    
    批量处理异步任务，控制并发。
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process(
        self,
        items: List[Any],
        process_fn: Callable[[Any], Coroutine],
    ) -> List[Any]:
        """
        处理批量任务
        
        Args:
            items: 项目列表
            process_fn: 处理函数
            
        Returns:
            结果列表
        """
        async def bounded_process(item):
            async with self._semaphore:
                return await process_fn(item)
        
        return await asyncio.gather(*[bounded_process(item) for item in items])


# 导出
__all__ = [
    "sleep",
    "wait_for",
    "gather_with_concurrency",
    "run_sync",
    "AsyncBatch",
]
