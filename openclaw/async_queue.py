"""
AsyncQueue - 异步队列
基于 Claude Code asyncQueue.ts 设计

异步队列实现。
"""
import asyncio
from typing import Any, Optional


class AsyncQueue:
    """
    异步队列
    
    线程安全的异步队列。
    """
    
    def __init__(self, maxsize: int = 0):
        """
        Args:
            maxsize: 最大大小，0表示无限制
        """
        self._queue = asyncio.Queue(maxsize=maxsize)
    
    async def put(self, item: Any) -> None:
        """放入项"""
        await self._queue.put(item)
    
    async def get(self) -> Any:
        """获取项"""
        return await self._queue.get()
    
    async def get_nowait(self) -> Optional[Any]:
        """非阻塞获取"""
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
    
    def put_nowait(self, item: Any) -> bool:
        """非阻塞放入"""
        try:
            self._queue.put_nowait(item)
            return True
        except asyncio.QueueFull:
            return False
    
    async def join(self) -> None:
        """等待队列清空"""
        await self._queue.join()
    
    def task_done(self) -> None:
        """标记任务完成"""
        self._queue.task_done()
    
    def qsize(self) -> int:
        """队列大小"""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """是否为空"""
        return self._queue.empty()
    
    def full(self) -> bool:
        """是否已满"""
        return self._queue.full()


class AsyncPriorityQueue:
    """
    异步优先级队列
    """
    
    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.PriorityQueue(maxsize=maxsize)
    
    async def put(self, item: Any, priority: int = 0) -> None:
        """放入项（优先级越低越先出）"""
        await self._queue.put((priority, item))
    
    async def get(self) -> Any:
        """获取项"""
        _, item = await self._queue.get()
        return item
    
    def get_nowait(self) -> Optional[Any]:
        """非阻塞获取"""
        try:
            _, item = self._queue.get_nowait()
            return item
        except asyncio.QueueEmpty:
            return None
    
    def qsize(self) -> int:
        return self._queue.qsize()


class AsyncBoundedQueue:
    """
    异步有界队列
    
    带背压的队列。
    """
    
    def __init__(self, maxsize: int = 100):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._waiting_getters: list = []
    
    async def put(self, item: Any) -> None:
        """放入项（队列满时阻塞）"""
        await self._queue.put(item)
        
        # 唤醒等待的getter
        if self._waiting_getters:
            getter = self._waiting_getters.pop(0)
            getter.set_result(item)
    
    async def get(self) -> Any:
        """获取项（队列空时阻塞）"""
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            future = asyncio.Future()
            self._waiting_getters.append(future)
            return await future
    
    def qsize(self) -> int:
        return self._queue.qsize()


# 导出
__all__ = [
    "AsyncQueue",
    "AsyncPriorityQueue",
    "AsyncBoundedQueue",
]
