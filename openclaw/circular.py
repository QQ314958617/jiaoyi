"""
Circular - 环
基于 Claude Code circular.ts 设计

循环缓冲工具。
"""
from typing import Any, List, Optional


class CircularBuffer:
    """
    循环缓冲区
    
    固定大小的FIFO缓冲区。
    """
    
    def __init__(self, capacity: int):
        """
        Args:
            capacity: 容量
        """
        self._capacity = capacity
        self._buffer: List[Any] = [None] * capacity
        self._head = 0  # 读位置
        self._tail = 0  # 写位置
        self._size = 0
    
    def push(self, item: Any) -> bool:
        """
        添加元素
        
        Returns:
            是否成功
        """
        if self._size >= self._capacity:
            return False
        
        self._buffer[self._tail] = item
        self._tail = (self._tail + 1) % self._capacity
        self._size += 1
        return True
    
    def pop(self) -> Optional[Any]:
        """
        取出元素
        
        Returns:
            元素或None
        """
        if self._size == 0:
            return None
        
        item = self._buffer[self._head]
        self._buffer[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._size -= 1
        return item
    
    def peek(self) -> Optional[Any]:
        """查看下一个元素"""
        if self._size == 0:
            return None
        return self._buffer[self._head]
    
    @property
    def size(self) -> int:
        return self._size
    
    @property
    def capacity(self) -> int:
        return self._capacity
    
    @property
    def is_empty(self) -> bool:
        return self._size == 0
    
    @property
    def is_full(self) -> bool:
        return self._size >= self._capacity
    
    def clear(self) -> None:
        """清空"""
        self._buffer = [None] * self._capacity
        self._head = 0
        self._tail = 0
        self._size = 0
    
    def to_list(self) -> List[Any]:
        """转换为列表"""
        if self._size == 0:
            return []
        
        if self._head < self._tail:
            return self._buffer[self._head:self._tail]
        else:
            return self._buffer[self._head:] + self._buffer[:self._tail]


class CircularIndex:
    """
    循环索引
    
    在固定范围内循环。
    """
    
    def __init__(self, size: int):
        """
        Args:
            size: 范围大小
        """
        self._size = size
        self._current = 0
    
    def next(self) -> int:
        """下一个索引"""
        value = self._current
        self._current = (self._current + 1) % self._size
        return value
    
    def prev(self) -> int:
        """上一个索引"""
        self._current = (self._current - 1 + self._size) % self._size
        return self._current
    
    @property
    def current(self) -> int:
        return self._current
    
    def reset(self, start: int = 0) -> None:
        """重置"""
        self._current = start % self._size


# 导出
__all__ = [
    "CircularBuffer",
    "CircularIndex",
]
