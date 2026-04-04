"""
Queue - 队列
基于 Claude Code queue.ts 设计

各种队列实现。
"""
import asyncio
import collections
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar('T')


class Queue(Generic[T]):
    """
    线程安全队列
    
    包装标准库queue.Queue。
    """
    
    def __init__(self, maxsize: int = 0):
        self._queue = collections.queue.Queue(maxsize=maxsize)
    
    def put(self, item: T, block: bool = True, timeout: float = None) -> None:
        """放入项目"""
        self._queue.put(item, block=block, timeout=timeout)
    
    def get(self, block: bool = True, timeout: float = None) -> T:
        """取出项目"""
        return self._queue.get(block=block, timeout=timeout)
    
    def put_nowait(self, item: T) -> None:
        """非阻塞放入"""
        self._queue.put_nowait(item)
    
    def get_nowait(self) -> T:
        """非阻塞取出"""
        return self._queue.get_nowait()
    
    def empty(self) -> bool:
        """是否为空"""
        return self._queue.empty()
    
    def full(self) -> bool:
        """是否已满"""
        return self._queue.full()
    
    def qsize(self) -> int:
        """大小"""
        return self._queue.qsize()


class PriorityQueue(Generic[T]):
    """
    优先级队列
    
    优先级高的项目先出队。
    """
    
    def __init__(self):
        self._heap = []
        self._counter = 0
        self._lock = collections.Lock()
    
    def put(self, item: T, priority: float = 0) -> None:
        """放入项目"""
        with self._lock:
            import heapq
            heapq.heappush(self._heap, (priority, self._counter, item))
            self._counter += 1
    
    def get(self) -> T:
        """取出最高优先级项目"""
        with self._lock:
            import heapq
            _, _, item = heapq.heappop(self._heap)
            return item
    
    def empty(self) -> bool:
        """是否为空"""
        return len(self._heap) == 0
    
    def qsize(self) -> int:
        """大小"""
        return len(self._heap)


class LIFOQueue(Generic[T]):
    """
    后进先出队列
    
    最后放入的项目先取出。
    """
    
    def __init__(self, maxsize: int = 0):
        self._queue = collections.queue.Queue(maxsize=maxsize)
    
    def put(self, item: T) -> None:
        """放入项目"""
        self._queue.put(item)
    
    def get(self) -> T:
        """取出最后放入的项目"""
        import queue
        return self._queue.get_nowait()


class AsyncQueue(Generic[T]):
    """
    异步队列
    """
    
    def __init__(self, maxsize: int = 0):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
    
    async def put(self, item: T) -> None:
        """放入项目"""
        await self._queue.put(item)
    
    async def get(self) -> T:
        """取出项目"""
        return await self._queue.get()
    
    async def put_nowait(self, item: T) -> None:
        """非阻塞放入"""
        self._queue.put_nowait(item)
    
    async def get_nowait(self) -> T:
        """非阻塞取出"""
        return self._queue.get_nowait()
    
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
    "Queue",
    "PriorityQueue",
    "LIFOQueue",
    "AsyncQueue",
]
