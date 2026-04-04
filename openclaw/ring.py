"""
Ring - 环
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
        self._head = 0  # 读取位置
        self._tail = 0  # 写入位置
        self._size = 0
    
    def push(self, item: Any) -> bool:
        """
        添加元素
        
        Args:
            item: 元素
            
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
        """
        查看下一个元素
        
        Returns:
            元素或None
        """
        if self._size == 0:
            return None
        return self._buffer[self._head]
    
    def get(self, index: int) -> Optional[Any]:
        """
        按索引获取
        
        Args:
            index: 索引
            
        Returns:
            元素或None
        """
        if index < 0 or index >= self._size:
            return None
        
        actual_index = (self._head + index) % self._capacity
        return self._buffer[actual_index]
    
    @property
    def size(self) -> int:
        """当前大小"""
        return self._size
    
    @property
    def capacity(self) -> int:
        """容量"""
        return self._capacity
    
    def is_empty(self) -> bool:
        """是否为空"""
        return self._size == 0
    
    def is_full(self) -> bool:
        """是否已满"""
        return self._size >= self._capacity
    
    def clear(self) -> None:
        """清空"""
        self._buffer = [None] * self._capacity
        self._head = 0
        self._tail = 0
        self._size = 0
    
    def to_list(self) -> List[Any]:
        """转换为列表"""
        result = []
        for i in range(self._size):
            result.append(self.get(i))
        return result


class CircularList:
    """
    循环列表
    
    支持循环遍历的列表。
    """
    
    def __init__(self, items: List[Any] = None):
        """
        Args:
            items: 初始元素
        """
        self._items = items or []
        self._current = 0
    
    def append(self, item: Any) -> None:
        """添加元素"""
        self._items.append(item)
    
    def next(self) -> Any:
        """
        获取下一个元素
        
        Returns:
            下一个元素
        """
        if not self._items:
            return None
        
        item = self._items[self._current]
        self._current = (self._current + 1) % len(self._items)
        return item
    
    @property
    def current(self) -> Any:
        """当前元素"""
        if not self._items:
            return None
        return self._items[self._current]
    
    def reset(self) -> None:
        """重置位置"""
        self._current = 0
    
    def __len__(self) -> int:
        return len(self._items)
    
    def __getitem__(self, index: int) -> Any:
        return self._items[index % len(self._items)]


# 导出
__all__ = [
    "RingBuffer",
    "CircularList",
]
