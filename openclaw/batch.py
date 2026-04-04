"""
Batch - 批量处理
基于 Claude Code batch.ts 设计

批量处理工具。
"""
import asyncio
from typing import Callable, Generic, List, TypeVar, Any

T = TypeVar('T')
R = TypeVar('R')


class Batch(Generic[T]):
    """
    批量处理器
    
    累积项目，达到阈值或超时时自动处理。
    """
    
    def __init__(
        self,
        processor: Callable[[List[T]], None],
        max_size: int = 100,
        max_wait_ms: int = 1000,
    ):
        """
        Args:
            processor: 批量处理器函数
            max_size: 最大批量大小
            max_wait_ms: 最大等待毫秒
        """
        self._processor = processor
        self._max_size = max_size
        self._max_wait_ms = max_wait_ms
        self._buffer: List[T] = []
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
    
    async def add(self, item: T) -> None:
        """添加项目"""
        async with self._lock:
            self._buffer.append(item)
            
            if len(self._buffer) >= self._max_size:
                await self._flush()
            elif self._task is None:
                self._task = asyncio.create_task(self._delayed_flush())
    
    async def _flush(self) -> None:
        """立即flush"""
        if not self._buffer:
            return
        
        items = self._buffer
        self._buffer = []
        self._task = None
        
        await asyncio.get_event_loop().run_in_executor(
            None, self._processor, items
        )
    
    async def _delayed_flush(self) -> None:
        """延迟flush"""
        await asyncio.sleep(self._max_wait_ms / 1000)
        async with self._lock:
            await self._flush()
    
    async def close(self) -> None:
        """关闭，flush剩余项"""
        async with self._lock:
            if self._task:
                self._task.cancel()
                self._task = None
            await self._flush()


class AsyncBatch(Generic[T, R]):
    """
    异步批量处理器
    
    支持返回结果的批量处理。
    """
    
    def __init__(
        self,
        processor: Callable[[List[T]], List[R]],
        max_size: int = 100,
        max_wait_ms: int = 1000,
    ):
        self._processor = processor
        self._max_size = max_size
        self._max_wait_ms = max_wait_ms
        self._buffer: List[T] = []
        self._futures: List[asyncio.Future] = []
        self._lock = asyncio.Lock()
    
    async def submit(self, item: T) -> List[R]:
        """提交项目并等待结果"""
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        
        async with self._lock:
            self._buffer.append((item, future))
            
            if len(self._buffer) >= self._max_size:
                await self._flush()
        
        return await future
    
    async def _flush(self) -> None:
        """flush处理"""
        if not self._buffer:
            return
        
        items = [item for item, _ in self._buffer]
        futures = [f for _, f in self._buffer]
        self._buffer = []
        
        try:
            results = await asyncio.get_event_loop().run_in_executor(
                None, self._processor, items
            )
            
            for future, result in zip(futures, results):
                if not future.done():
                    future.set_result(result)
        except Exception as e:
            for future in futures:
                if not future.done():
                    future.set_exception(e)


def batch_items(
    items: List[T],
    batch_size: int,
) -> List[List[T]]:
    """
    将列表分批
    
    Args:
        items: 列表
        batch_size: 批量大小
        
    Returns:
        分批后的列表
    """
    return [items[i:i+batch_size] for i in range(0, len(items), batch_size)]


# 导出
__all__ = [
    "Batch",
    "AsyncBatch",
    "batch_items",
]
