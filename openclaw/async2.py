"""
Async2 - 异步
基于 Claude Code async.ts 设计

异步工具。
"""
import asyncio
from typing import Any, Callable, List


async def sleep(seconds: float) -> None:
    """
    异步延迟
    
    Args:
        seconds: 秒数
    """
    await asyncio.sleep(seconds)


async def wait_for(coro, timeout: float) -> Any:
    """
    异步等待超时
    
    Args:
        coro: 协程
        timeout: 超时时间
        
    Returns:
        协程结果
    """
    return await asyncio.wait_for(coro, timeout=timeout)


async def gather(*coros) -> List[Any]:
    """
    并发执行多个协程
    
    Args:
        *coros: 协程列表
        
    Returns:
        结果列表
    """
    return await asyncio.gather(*coros)


async def race(*coros) -> Any:
    """
    返回最快完成的结果
    
    Args:
        *coros: 协程列表
        
    Returns:
        最快协程的结果
    """
    done, pending = await asyncio.wait(
        [asyncio.create_task(c) for c in coros],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    for task in pending:
        task.cancel()
    
    return done.pop().result()


async def timeout_after(seconds: float, coro):
    """
    超时包装
    
    Args:
        seconds: 超时时间
        coro: 协程
        
    Returns:
        (success, result)
    """
    try:
        result = await asyncio.wait_for(coro, timeout=seconds)
        return True, result
    except asyncio.TimeoutError:
        return False, None


def run_async(fn: Callable) -> Callable:
    """
    在事件循环中运行异步函数
    
    Args:
        fn: 异步函数
        
    Returns:
        同步包装函数
    """
    def wrapper(*args, **kwargs):
        return asyncio.run(fn(*args, **kwargs))
    return wrapper


class AsyncQueue:
    """
    异步队列
    """
    
    def __init__(self, maxsize: int = 0):
        """
        Args:
            maxsize: 最大大小（0无限）
        """
        self._queue = asyncio.Queue(maxsize=maxsize)
    
    async def put(self, item: Any) -> None:
        """放入"""
        await self._queue.put(item)
    
    async def get(self) -> Any:
        """取出"""
        return await self._queue.get()
    
    def empty(self) -> bool:
        """是否为空"""
        return self._queue.empty()
    
    def full(self) -> bool:
        """是否已满"""
        return self._queue.full()
    
    def qsize(self) -> int:
        """大小"""
        return self._queue.qsize()


# 导出
__all__ = [
    "sleep",
    "wait_for",
    "gather",
    "race",
    "timeout_after",
    "run_async",
    "AsyncQueue",
]
