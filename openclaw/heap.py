"""
Heap - 堆
基于 Claude Code heap.ts 设计

二叉堆实现。
"""
from typing import Any, Callable, List, Optional


class MinHeap:
    """
    最小堆
    
    O(log n) 插入和删除最小值。
    """
    
    def __init__(self, key: Callable[[Any], Any] = None):
        """
        Args:
            key: 比较键函数
        """
        self._data: List[Any] = []
        self._key = key or (lambda x: x)
    
    def _compare(self, i: int, j: int) -> bool:
        """比较两个元素"""
        return self._key(self._data[i]) < self._key(self._data[j])
    
    def _parent(self, i: int) -> int:
        return (i - 1) // 2
    
    def _left(self, i: int) -> int:
        return 2 * i + 1
    
    def _right(self, i: int) -> int:
        return 2 * i + 2
    
    def _swap(self, i: int, j: int) -> None:
        self._data[i], self._data[j] = self._data[j], self._data[i]
    
    def _sift_up(self, i: int) -> None:
        """向上筛选"""
        while i > 0:
            parent = self._parent(i)
            if self._compare(i, parent):
                self._swap(i, parent)
                i = parent
            else:
                break
    
    def _sift_down(self, i: int) -> None:
        """向下筛选"""
        size = len(self._data)
        
        while True:
            smallest = i
            left = self._left(i)
            right = self._right(i)
            
            if left < size and self._compare(left, smallest):
                smallest = left
            
            if right < size and self._compare(right, smallest):
                smallest = right
            
            if smallest != i:
                self._swap(i, smallest)
                i = smallest
            else:
                break
    
    def push(self, item: Any) -> None:
        """添加元素"""
        self._data.append(item)
        self._sift_up(len(self._data) - 1)
    
    def pop(self) -> Optional[Any]:
        """弹出最小元素"""
        if not self._data:
            return None
        
        result = self._data[0]
        last = self._data.pop()
        
        if self._data:
            self._data[0] = last
            self._sift_down(0)
        
        return result
    
    def peek(self) -> Optional[Any]:
        """查看最小元素"""
        return self._data[0] if self._data else None
    
    def size(self) -> int:
        """堆大小"""
        return len(self._data)
    
    def is_empty(self) -> bool:
        """是否为空"""
        return len(self._data) == 0
    
    def __len__(self) -> int:
        return self.size()
    
    def __iter__(self):
        return iter(self._data)


class MaxHeap(MinHeap):
    """最大堆"""
    
    def _compare(self, i: int, j: int) -> bool:
        return self._key(self._data[i]) > self._key(self._data[j])


def heap_sort(items: List[Any], reverse: bool = False) -> List[Any]:
    """
    堆排序
    
    Args:
        items: 要排序的列表
        reverse: 是否降序
        
    Returns:
        排序后的列表
    """
    if reverse:
        heap = MaxHeap()
    else:
        heap = MinHeap()
    
    for item in items:
        heap.push(item)
    
    result = []
    while not heap.is_empty():
        result.append(heap.pop())
    
    return result


# 导出
__all__ = [
    "MinHeap",
    "MaxHeap",
    "heap_sort",
]
