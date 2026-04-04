"""
Heap - 堆数据结构
基于 Claude Code heap.ts 设计

最小堆和最大堆实现。
"""
import heapq
from typing import Any, Callable, List, Optional


class MinHeap:
    """
    最小堆
    
    始终返回最小的元素。
    """
    
    def __init__(self):
        self._heap: List[Any] = []
    
    def push(self, item: Any) -> None:
        """添加元素"""
        heapq.heappush(self._heap, item)
    
    def pop(self) -> Any:
        """弹出最小元素"""
        if not self._heap:
            raise IndexError("pop from empty heap")
        return heapq.heappop(self._heap)
    
    def peek(self) -> Optional[Any]:
        """查看最小元素"""
        if not self._heap:
            return None
        return self._heap[0]
    
    def pushpop(self, item: Any) -> Any:
        """先添加再弹出"""
        return heapq.heappushpop(self._heap, item)
    
    def replace(self, item: Any) -> Any:
        """先弹出再添加"""
        if not self._heap:
            raise IndexError("replace from empty heap")
        return heapq.heapreplace(self._heap, item)
    
    def __len__(self) -> int:
        return len(self._heap)
    
    def __bool__(self) -> bool:
        return bool(self._heap)
    
    def clear(self) -> None:
        """清空堆"""
        self._heap.clear()
    
    def get_all(self) -> List[Any]:
        """获取所有元素（无序）"""
        return list(self._heap)


class MaxHeap:
    """
    最大堆
    
    始终返回最大的元素。
    使用最小堆实现，元素取反。
    """
    
    def __init__(self):
        self._heap: List[Any] = []
    
    def push(self, item: Any) -> None:
        """添加元素（取反）"""
        heapq.heappush(self._heap, -item)
    
    def pop(self) -> Any:
        """弹出最大元素"""
        if not self._heap:
            raise IndexError("pop from empty heap")
        return -heapq.heappop(self._heap)
    
    def peek(self) -> Optional[Any]:
        """查看最大元素"""
        if not self._heap:
            return None
        return -self._heap[0]
    
    def pushpop(self, item: Any) -> Any:
        """先添加再弹出"""
        return -heapq.heappushpop(self._heap, -item)
    
    def replace(self, item: Any) -> Any:
        """先弹出再添加"""
        if not self._heap:
            raise IndexError("replace from empty heap")
        return -heapq.heapreplace(self._heap, -item)
    
    def __len__(self) -> int:
        return len(self._heap)
    
    def __bool__(self) -> bool:
        return bool(self._heap)
    
    def clear(self) -> None:
        """清空堆"""
        self._heap.clear()


class HeapItem:
    """
    堆元素包装器
    
    用于当元素本身可比较性不足时。
    """
    
    def __init__(self, priority: float, value: Any):
        self.priority = priority
        self.value = value
    
    def __lt__(self, other: "HeapItem") -> bool:
        return self.priority < other.priority
    
    def __le__(self, other: "HeapItem") -> bool:
        return self.priority <= other.priority
    
    def __gt__(self, other: "HeapItem") -> bool:
        return self.priority > other.priority
    
    def __ge__(self, other: "HeapItem") -> bool:
        return self.priority >= other.priority
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, HeapItem):
            return False
        return self.priority == other.priority
    
    def __repr__(self) -> str:
        return f"HeapItem({self.priority}, {self.value!r})"


def heap_sort(items: List[Any], reverse: bool = False) -> List[Any]:
    """
    堆排序
    
    Args:
        items: 要排序的列表
        reverse: 是否降序
        
    Returns:
        排序后的新列表
    """
    if reverse:
        heap = [(-x, x) for x in items]
        heapq.heapify(heap)
        return [heapq.heappop(heap)[1] for _ in range(len(heap))]
    else:
        heap = [(x, x) for x in items]
        heapq.heapify(heap)
        return [heapq.heappop(heap)[0] for _ in range(len(heap))]


def find_k_largest(items: List[Any], k: int) -> List[Any]:
    """
    找到第k大的元素
    
    使用堆排序，返回最大的k个元素。
    
    Args:
        items: 列表
        k: k值
        
    Returns:
        最大的k个元素
    """
    if k >= len(items):
        return sorted(items, reverse=True)
    
    # 使用最小堆维护k个最大元素
    heap = items[:k]
    heapq.heapify(heap)
    
    for item in items[k:]:
        if item > heap[0]:
            heapq.heapreplace(heap, item)
    
    return sorted(heap, reverse=True)


def find_k_smallest(items: List[Any], k: int) -> List[Any]:
    """
    找到第k小的元素
    
    使用最大堆维护k个最小元素。
    
    Args:
        items: 列表
        k: k值
        
    Returns:
        最小的k个元素
    """
    if k >= len(items):
        return sorted(items)
    
    # 使用最大堆
    heap = [-x for x in items[:k]]
    heapq.heapify(heap)
    
    for i, item in enumerate(items[k:]):
        if item < -heap[0]:
            heapq.heapreplace(heap, -item)
    
    return sorted([-x for x in heap])


# 导出
__all__ = [
    "MinHeap",
    "MaxHeap",
    "HeapItem",
    "heap_sort",
    "find_k_largest",
    "find_k_smallest",
]
