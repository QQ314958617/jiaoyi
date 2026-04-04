"""
Stream - 流式处理
基于 Claude Code stream.ts 设计

异步流处理工具。
"""
import asyncio
from typing import AsyncIterator, Callable, Generic, TypeVar, Optional, AsyncGenerator

T = TypeVar('T')
U = TypeVar('U')


class Stream(Generic[T]):
    """
    异步流
    
    支持入队、出队、完成、错误处理。
    """
    
    def __init__(self, on_return: Optional[Callable] = None):
        """
        Args:
            on_return: 迭代结束时调用的函数
        """
        self._queue: asyncio.Queue = asyncio.Queue()
        self._on_return = on_return
        self._is_done = False
        self._has_error = False
        self._error: Optional[Exception] = None
        self._read_waiter: Optional[asyncio.Future] = None
        self._started = False
    
    def __aiter__(self) -> AsyncIterator[T]:
        """返回异步迭代器"""
        if self._started:
            raise ValueError("Stream can only be iterated once")
        self._started = True
        return self
    
    async def __anext__(self) -> T:
        """异步迭代下一步"""
        if self._queue.qsize() > 0:
            return self._queue.get_nowait()
        
        if self._is_done:
            raise StopAsyncIteration
        
        if self._has_error and self._error:
            raise self._error
        
        # 创建等待
        self._read_waiter = asyncio.get_event_loop().create_future()
        
        try:
            value = await self._read_waiter
            if self._has_error and self._error:
                raise self._error
            return value
        except asyncio.CancelledError:
            raise StopAsyncIteration
    
    async def enqueue(self, value: T) -> None:
        """
        入队
        
        Args:
            value: 值
        """
        if self._read_waiter and not self._read_waiter.done():
            waiter = self._read_waiter
            self._read_waiter = None
            waiter.set_result(value)
        else:
            await self._queue.put(value)
    
    async def done(self) -> None:
        """标记流完成"""
        self._is_done = True
        
        if self._read_waiter and not self._read_waiter.done():
            waiter = self._read_waiter
            self._read_waiter = None
            waiter.set_result(None)  # 发送结束信号
    
    async def error(self, err: Exception) -> None:
        """
        标记流错误
        
        Args:
            err: 错误
        """
        self._has_error = True
        self._error = err
        
        if self._read_waiter and not self._read_waiter.done():
            waiter = self._read_waiter
            self._read_waiter = None
            waiter.set_exception(err)
    
    async def aclose(self) -> None:
        """关闭流"""
        self._is_done = True
        if self._on_return:
            try:
                self._on_return()
            except Exception:
                pass


async def stream_from_async_generator(
    gen: AsyncGenerator[T, None],
) -> Stream[T]:
    """
    从异步生成器创建流
    
    Args:
        gen: 异步生成器
        
    Returns:
        Stream
    """
    stream = Stream[T]()
    
    async def consume():
        try:
            async for item in gen:
                await stream.enqueue(item)
            await stream.done()
        except Exception as e:
            await stream.error(e)
    
    asyncio.create_task(consume())
    return stream


async def stream_map(
    stream: Stream[T],
    fn: Callable[[T], U],
) -> Stream[U]:
    """
    流映射
    
    Args:
        stream: 输入流
        fn: 映射函数
        
    Returns:
        输出流
    """
    output = Stream[U]()
    
    async def mapper():
        async for item in stream:
            try:
                result = fn(item)
                if asyncio.iscoroutine(result):
                    result = await result
                await output.enqueue(result)
            except Exception as e:
                await output.error(e)
                return
        await output.done()
    
    asyncio.create_task(mapper())
    return output


async def stream_filter(
    stream: Stream[T],
    predicate: Callable[[T], bool],
) -> Stream[T]:
    """
    流过滤
    
    Args:
        stream: 输入流
        predicate: 过滤函数
        
    Returns:
        输出流
    """
    output = Stream[T]()
    
    async def filter():
        async for item in stream:
            try:
                keep = predicate(item)
                if asyncio.iscoroutine(keep):
                    keep = await keep
                if keep:
                    await output.enqueue(item)
            except Exception as e:
                await output.error(e)
                return
        await output.done()
    
    asyncio.create_task(filter())
    return output


async def stream_batch(
    stream: Stream[T],
    size: int,
) -> Stream[list[T]]:
    """
    流批量处理
    
    Args:
        stream: 输入流
        size: 批量大小
        
    Returns:
        输出流（批量）
    """
    output = Stream[list[T]]()
    
    async def batcher():
        batch = []
        async for item in stream:
            batch.append(item)
            if len(batch) >= size:
                await output.enqueue(batch)
                batch = []
        if batch:
            await output.enqueue(batch)
        await output.done()
    
    asyncio.create_task(batcher())
    return output


# 导出
__all__ = [
    "Stream",
    "stream_from_async_generator",
    "stream_map",
    "stream_filter",
    "stream_batch",
]
