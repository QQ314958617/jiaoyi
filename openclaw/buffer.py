"""
Buffer - 缓冲区
基于 Claude Code buffer.ts 设计

缓冲区工具。
"""
from typing import Any, List, Optional


class Buffer:
    """
    缓冲区
    
    固定大小的数据缓冲。
    """
    
    def __init__(self, capacity: int):
        """
        Args:
            capacity: 容量
        """
        self._capacity = capacity
        self._data: List[Any] = []
        self._position = 0
    
    def write(self, item: Any) -> bool:
        """
        写入
        
        Args:
            item: 数据项
            
        Returns:
            是否成功
        """
        if len(self._data) < self._capacity:
            self._data.append(item)
            return True
        return False
    
    def write_overwrite(self, item: Any) -> Any:
        """
        写入（溢出时覆盖最旧的）
        
        Args:
            item: 数据项
            
        Returns:
            被覆盖的数据项
        """
        overwritten = None
        
        if len(self._data) >= self._capacity:
            overwritten = self._data[self._position]
            self._data[self._position] = item
            self._position = (self._position + 1) % self._capacity
        else:
            self._data.append(item)
        
        return overwritten
    
    def read(self) -> Optional[Any]:
        """
        读取最旧的数据
        
        Returns:
            数据项或None
        """
        if not self._data:
            return None
        
        item = self._data[self._position]
        self._data[self._position] = None
        
        if self._position == 0 and len(self._data) == 1:
            self._data.clear()
        else:
            self._position = (self._position + 1) % self._capacity
        
        return item
    
    def peek(self) -> Optional[Any]:
        """查看最旧数据"""
        if self._data:
            return self._data[self._position]
        return None
    
    def clear(self) -> None:
        """清空"""
        self._data.clear()
        self._position = 0
    
    @property
    def size(self) -> int:
        """当前大小"""
        if not self._data:
            return 0
        if len(self._data) < self._capacity:
            return len(self._data)
        return self._capacity
    
    @property
    def capacity(self) -> int:
        """容量"""
        return self._capacity
    
    @property
    def is_empty(self) -> bool:
        return len(self._data) == 0
    
    @property
    def is_full(self) -> bool:
        return len(self._data) >= self._capacity
    
    def to_list(self) -> List[Any]:
        """转为列表"""
        if not self._data:
            return []
        if len(self._data) < self._capacity:
            return list(self._data)
        return self._data[self._position:] + self._data[:self._position]


class CircularBuffer:
    """循环缓冲区（别名）"""
    
    def __init__(self, capacity: int):
        self._buffer = Buffer(capacity)
    
    def push(self, item: Any) -> bool:
        return self._buffer.write(item)
    
    def pop(self) -> Optional[Any]:
        return self._buffer.read()
    
    def peek(self) -> Optional[Any]:
        return self._buffer.peek()
    
    def clear(self) -> None:
        self._buffer.clear()
    
    @property
    def size(self) -> int:
        return self._buffer.size
    
    @property
    def capacity(self) -> int:
        return self._buffer.capacity
    
    @property
    def is_empty(self) -> bool:
        return self._buffer.is_empty
    
    @property
    def is_full(self) -> bool:
        return self._buffer.is_full


# 导出
__all__ = [
    "Buffer",
    "CircularBuffer",
]
