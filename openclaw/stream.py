"""
OpenClaw Async Stream
=====================
Inspired by Claude Code's src/utils/stream.ts (76 lines).

AsyncIterator 实现，支持：
- enqueue(value) - 添加数据
- done() - 标记完成
- error(ex) - 错误传播
- for await ... 语法

Python 对等实现：asyncio.Queue 已经提供类似功能，
但这个版本更轻量，适合同步上下文。
"""

from __future__ import annotations

import asyncio
from typing import Generic, TypeVar, Optional, Callable, Awaitable

T = TypeVar('T')

class AsyncStream(Generic[T]):
    """
    异步数据流
    
    Claude Code 模式：
    - queue: 缓冲区，未被 next() 消费的值
    - read_resolve/read_reject: pending next() 的 future
    - is_done: 流已结束
    - has_error: 错误状态
    
    用法：
    ```python
    stream = AsyncStream[int]()
    
    async def producer():
        for i in range(5):
            stream.enqueue(i)
        stream.done()
    
    async def consumer():
        async for value in stream:
            print(value)
    
    asyncio.run(consumer())
    ```
    """
    
    def __init__(self, returned: Optional[Callable[[], None]] = None):
        self._queue: list[T] = []
        self._read_future: Optional[asyncio.Future] = None
        self._is_done: bool = False
        self._has_error: Optional[Exception] = None
        self._started: bool = False
        self._returned = returned
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        return self._loop
    
    def __aiter__(self) -> 'AsyncStream[T]':
        if self._started:
            raise ValueError("AsyncStream can only be iterated once")
        self._started = True
        return self
    
    async def __anext__(self) -> T:
        loop = self._get_loop()
        
        # 有排队的值
        if self._queue:
            return self._queue.pop(0)
        
        # 已结束
        if self._is_done:
            raise StopAsyncIteration
        
        # 有错误
        if self._has_error:
            raise self._has_error
        
        # 创建新的 future 等待值
        if self._read_future is not None and not self._read_future.done():
            # 已有 pending 的 future，先完成它
            pass
        else:
            self._read_future = loop.create_future()
        
        try:
            result = await self._read_future
            self._read_future = None
        except StopAsyncIteration:
            raise
        except Exception as e:
            self._read_future = None
            raise
        
        if isinstance(result, Exception):
            raise result
        
        if result is None or (isinstance(result, dict) and result.get("done")):
            raise StopAsyncIteration
        
        return result
    
    def enqueue(self, value: T) -> None:
        """添加一个值到流"""
        if self._is_done:
            raise ValueError("Cannot enqueue to a done stream")
        
        if self._read_future is not None and not self._read_future.done():
            # 有 pending 的消费者，立即传递值
            future = self._read_future
            self._read_future = None
            if not future.done():
                future.set_result(value)
        else:
            self._queue.append(value)
    
    def done(self) -> None:
        """标记流结束"""
        self._is_done = True
        if self._read_future is not None and not self._read_future.done():
            future = self._read_future
            self._read_future = None
            future.set_result(None)  # None 表示结束
    
    def error(self, ex: Exception) -> None:
        """标记流出错"""
        self._has_error = ex
        if self._read_future is not None and not self._read_future.done():
            future = self._read_future
            self._read_future = None
            future.set_exception(ex)
    
    async def __aenter__(self) -> 'AsyncStream[T]':
        return self

    async def __aexit__(self, *args) -> None:
        self.done()
        if self._returned:
            self._returned()


class SyncStream(Generic[T]):
    """
    同步版本的数据流（用于非异步上下文）
    
    使用 threading.Lock + list 实现
    """
    
    def __init__(self):
        self._queue: list[T] = []
        self._is_done: bool = False
        self._has_error: Optional[Exception] = None
        self._started: bool = False
        self._lock = __import__('threading').Lock()
    
    def __iter__(self) -> 'SyncStream[T]':
        if self._started:
            raise ValueError("SyncStream can only be iterated once")
        self._started = True
        return self
    
    def __next__(self) -> T:
        import time
        
        if self._has_error:
            raise self._has_error
        
        # 等待值
        while not self._queue and not self._is_done:
            time.sleep(0.01)
        
        if self._queue:
            return self._queue.pop(0)
        
        if self._is_done:
            raise StopIteration
        
        raise RuntimeError("Stream in unexpected state")
    
    def enqueue(self, value: T) -> None:
        if self._is_done:
            raise ValueError("Cannot enqueue to a done stream")
        with self._lock:
            self._queue.append(value)
    
    def done(self) -> None:
        self._is_done = True
    
    def error(self, ex: Exception) -> None:
        self._has_error = ex
