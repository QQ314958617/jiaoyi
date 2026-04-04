"""
Buffer - 缓冲区
基于 Claude Code buffer.ts 设计

各种缓冲数据结构。
"""
from collections import deque
from typing import Callable, Generic, TypeVar, Optional

T = TypeVar('T')


class RingBuffer(Generic[T]):
    """
    环形缓冲区
    
    固定大小的缓冲区，新元素覆盖最旧的元素。
    """
    
    def __init__(self, capacity: int):
        """
        Args:
            capacity: 容量
        """
        self._capacity = capacity
        self._buffer: deque = deque(maxlen=capacity)
    
    def append(self, item: T) -> None:
        """添加元素"""
        self._buffer.append(item)
    
    def get_all(self) -> list[T]:
        """获取所有元素"""
        return list(self._buffer)
    
    def get_recent(self, n: int) -> list[T]:
        """获取最近的n个元素"""
        if n >= len(self._buffer):
            return list(self._buffer)
        return list(self._buffer)[-n:]
    
    def clear(self) -> None:
        """清空缓冲区"""
        self._buffer.clear()
    
    def __len__(self) -> int:
        return len(self._buffer)
    
    def __bool__(self) -> bool:
        return bool(self._buffer)
    
    @property
    def capacity(self) -> int:
        """容量"""
        return self._capacity


class SlidingWindowBuffer(Generic[T]):
    """
    滑动窗口缓冲区
    
    只保留时间窗口内的元素。
    """
    
    def __init__(self, max_age_seconds: float):
        """
        Args:
            max_age_seconds: 最大存活时间（秒）
        """
        import time
        self._max_age = max_age_seconds
        self._buffer: deque = deque()
        self._timestamps: deque = deque()
    
    def append(self, item: T) -> None:
        """添加元素"""
        import time
        now = time.time()
        self._buffer.append(item)
        self._timestamps.append(now)
        self._cleanup()
    
    def _cleanup(self) -> None:
        """清理过期元素"""
        import time
        now = time.time()
        cutoff = now - self._max_age
        
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
            if self._buffer:
                self._buffer.popleft()
    
    def get_all(self) -> list[T]:
        """获取所有未过期的元素"""
        self._cleanup()
        return list(self._buffer)
    
    def clear(self) -> None:
        """清空缓冲区"""
        self._buffer.clear()
        self._timestamps.clear()
    
    def __len__(self) -> int:
        self._cleanup()
        return len(self._buffer)
    
    def __bool__(self) -> bool:
        self._cleanup()
        return bool(self._buffer)


class AccumulatingBuffer(Generic[T]):
    """
    累积缓冲区
    
    累积元素直到达到阈值，然后处理。
    """
    
    def __init__(
        self,
        threshold: int,
        flush_fn: Callable[[list[T]], None],
        max_size: int = None,
    ):
        """
        Args:
            threshold: 触发flush的阈值
            flush_fn: 达到阈值时调用的flush函数
            max_size: 最大累积数（超过强制flush）
        """
        self._threshold = threshold
        self._flush_fn = flush_fn
        self._max_size = max_size or threshold * 2
        self._buffer: list[T] = []
    
    def append(self, item: T) -> None:
        """添加元素"""
        self._buffer.append(item)
        
        if len(self._buffer) >= self._threshold:
            self.flush()
    
    def flush(self) -> None:
        """手动flush"""
        if not self._buffer:
            return
        
        items = self._buffer
        self._buffer = []
        self._flush_fn(items)
    
    def __len__(self) -> int:
        return len(self._buffer)
    
    def __bool__(self) -> bool:
        return bool(self._buffer)


# 导出
__all__ = [
    "RingBuffer",
    "SlidingWindowBuffer",
    "AccumulatingBuffer",
]
