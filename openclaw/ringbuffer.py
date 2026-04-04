"""
RingBuffer - 环形缓冲区
基于 Claude Code ring.ts 设计

环形缓冲区实现。
"""
from typing import Any, List, Optional


class RingBuffer:
    """
    环形缓冲区
    
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
        
        Args:
            item: 元素
            
        Returns:
            是否成功（缓冲区满返回False）
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
    
    def push_overwrite(self, item: Any) -> None:
        """
        添加元素（溢出时覆盖最旧的）
        
        Args:
            item: 元素
        """
        if self._size == self._capacity:
            self._buffer[self._head] = item
            self._head = (self._head + 1) % self._capacity
        else:
            self._buffer[self._tail] = item
            self._tail = (self._tail + 1) % self._capacity
            self._size += 1
    
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
        return self._size == self._capacity
    
    def clear(self) -> None:
        """清空"""
        self._buffer = [None] * self._capacity
        self._head = 0
        self._tail = 0
        self._size = 0
    
    def to_list(self) -> List[Any]:
        """转为列表"""
        if self._size == 0:
            return []
        
        result = []
        index = self._head
        for _ in range(self._size):
            result.append(self._buffer[index])
            index = (index + 1) % self._capacity
        return result


# 导出
__all__ = [
    "RingBuffer",
]
