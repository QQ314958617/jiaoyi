"""
Queue2 - 队列
基于 Claude Code queue.ts 设计

队列数据结构。
"""
from typing import Any, List, Optional


class Queue:
    """
    队列
    """
    
    def __init__(self):
        self._data: List = []
    
    def enqueue(self, item: Any) -> None:
        """入队"""
        self._data.append(item)
    
    def dequeue(self) -> Optional[Any]:
        """出队"""
        if self._data:
            return self._data.pop(0)
        return None
    
    def peek(self) -> Optional[Any]:
        """查看队首"""
        if self._data:
            return self._data[0]
        return None
    
    def is_empty(self) -> bool:
        return len(self._data) == 0
    
    def size(self) -> int:
        return len(self._data)
    
    def clear(self) -> None:
        self._data.clear()
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __iter__(self):
        return iter(self._data)
    
    def to_list(self) -> List:
        return list(self._data)


class PriorityQueue:
    """
    优先队列
    """
    
    def __init__(self, key: callable = None, reverse: bool = False):
        """
        Args:
            key: 优先级键函数
            reverse: 是否反向（高优先级先出）
        """
        self._data: List = []
        self._key = key or (lambda x: x)
        self._reverse = reverse
    
    def _compare(self, a: Any, b: Any) -> bool:
        ka = self._key(a)
        kb = self._key(b)
        if self._reverse:
            return ka > kb
        return ka < kb
    
    def enqueue(self, item: Any) -> None:
        """入队"""
        self._data.append(item)
        self._sift_up(len(self._data) - 1)
    
    def _sift_up(self, i: int) -> None:
        while i > 0:
            parent = (i - 1) // 2
            if self._compare(self._data[i], self._data[parent]):
                self._data[i], self._data[parent] = self._data[parent], self._data[i]
                i = parent
            else:
                break
    
    def dequeue(self) -> Optional[Any]:
        """出队"""
        if not self._data:
            return None
        
        result = self._data[0]
        last = self._data.pop()
        
        if self._data:
            self._data[0] = last
            self._sift_down(0)
        
        return result
    
    def _sift_down(self, i: int) -> None:
        n = len(self._data)
        
        while True:
            smallest = i
            left = 2 * i + 1
            right = 2 * i + 2
            
            if left < n and self._compare(self._data[left], self._data[smallest]):
                smallest = left
            if right < n and self._compare(self._data[right], self._data[smallest]):
                smallest = right
            
            if smallest != i:
                self._data[i], self._data[smallest] = self._data[smallest], self._data[i]
                i = smallest
            else:
                break
    
    def peek(self) -> Optional[Any]:
        return self._data[0] if self._data else None
    
    def is_empty(self) -> bool:
        return len(self._data) == 0
    
    def size(self) -> int:
        return len(self._data)


# 导出
__all__ = [
    "Queue",
    "PriorityQueue",
]
