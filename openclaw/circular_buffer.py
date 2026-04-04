"""
Circular Buffer - 环形缓冲区
基于 Claude Code CircularBuffer.ts 设计

固定大小的环形缓冲区，当缓冲区满时自动移除最旧的元素。
"""
from typing import Generic, Iterator, List, Optional, TypeVar

T = TypeVar('T')


class CircularBuffer(Generic[T]):
    """
    固定大小环形缓冲区
    
    当缓冲区满时，新元素覆盖最旧的元素。
    """
    
    def __init__(self, capacity: int):
        """
        Args:
            capacity: 缓冲区容量
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        self._capacity = capacity
        self._buffer: List[Optional[T]] = [None] * capacity
        self._head = 0
        self._size = 0
    
    def add(self, item: T) -> None:
        """
        添加元素到缓冲区
        
        Args:
            item: 要添加的元素
        """
        self._buffer[self._head] = item
        self._head = (self._head + 1) % self._capacity
        
        if self._size < self._capacity:
            self._size += 1
    
    def add_all(self, items: list[T]) -> None:
        """
        批量添加元素
        
        Args:
            items: 要添加的元素列表
        """
        for item in items:
            self.add(item)
    
    def get_recent(self, count: int) -> list[T]:
        """
        获取最近的N个元素
        
        Args:
            count: 要获取的元素数量
            
        Returns:
            最近的元素列表
        """
        if self._size == 0:
            return []
        
        result = []
        available = min(count, self._size)
        
        # 计算起始位置
        if self._size < self._capacity:
            start = 0
        else:
            start = self._head
        
        for i in range(available):
            index = (start + self._size - available + i) % self._capacity
            result.append(self._buffer[index])
        
        return result
    
    def to_array(self) -> list[T]:
        """
        获取所有元素（从旧到新）
        
        Returns:
            所有元素的列表
        """
        if self._size == 0:
            return []
        
        result = []
        
        if self._size < self._capacity:
            start = 0
        else:
            start = self._head
        
        for i in range(self._size):
            index = (start + i) % self._capacity
            result.append(self._buffer[index])
        
        return result
    
    def clear(self) -> None:
        """清空缓冲区"""
        self._buffer = [None] * self._capacity
        self._head = 0
        self._size = 0
    
    def length(self) -> int:
        """
        获取当前元素数量
        
        Returns:
            元素数量
        """
        return self._size
    
    def is_full(self) -> bool:
        """
        检查缓冲区是否已满
        
        Returns:
            是否已满
        """
        return self._size == self._capacity
    
    def is_empty(self) -> bool:
        """
        检查缓冲区是否为空
        
        Returns:
            是否为空
        """
        return self._size == 0
    
    def peek(self) -> Optional[T]:
        """
        查看最旧的元素
        
        Returns:
            最旧的元素或None
        """
        if self._size == 0:
            return None
        
        if self._size < self._capacity:
            return self._buffer[0]
        
        index = self._head
        return self._buffer[index]
    
    def peek_last(self) -> Optional[T]:
        """
        查看最新的元素
        
        Returns:
            最新的元素或None
        """
        if self._size == 0:
            return None
        
        index = (self._head - 1 + self._capacity) % self._capacity
        return self._buffer[index]
    
    def __len__(self) -> int:
        return self._size
    
    def __repr__(self) -> str:
        return f"CircularBuffer(capacity={self._capacity}, size={self._size})"


# 导出
__all__ = [
    "CircularBuffer",
]
