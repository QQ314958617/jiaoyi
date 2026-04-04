"""
Sorted - 有序集合
基于 Claude Code sorted.ts 设计

有序集合实现。
"""
from typing import Any, Callable, List


class SortedList:
    """
    有序列表
    
    保持元素有序。
    """
    
    def __init__(self, key: Callable = None, reverse: bool = False):
        """
        Args:
            key: 排序键函数
            reverse: 是否降序
        """
        self._key = key or (lambda x: x)
        self._reverse = reverse
        self._data: List[Any] = []
    
    def _sort_key(self, item):
        """获取排序键"""
        return self._key(item)
    
    def add(self, item: Any) -> None:
        """添加元素"""
        key = self._sort_key(item)
        
        # 二分查找插入位置
        lo, hi = 0, len(self._data)
        
        while lo < hi:
            mid = (lo + hi) // 2
            mid_key = self._sort_key(self._data[mid])
            
            if (mid_key < key) != self._reverse:
                lo = mid + 1
            else:
                hi = mid
        
        self._data.insert(lo, item)
    
    def update(self, items: List[Any]) -> None:
        """批量添加"""
        for item in items:
            self.add(item)
    
    def remove(self, item: Any) -> bool:
        """移除元素"""
        try:
            self._data.remove(item)
            return True
        except ValueError:
            return False
    
    def pop(self, index: int = -1) -> Any:
        """弹出元素"""
        return self._data.pop(index)
    
    def clear(self) -> None:
        """清空"""
        self._data.clear()
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __contains__(self, item: Any) -> bool:
        return item in self._data
    
    def __getitem__(self, index: int) -> Any:
        return self._data[index]
    
    def __iter__(self):
        return iter(self._data)
    
    def to_list(self) -> List[Any]:
        return list(self._data)


def sort(items: List[Any], key: Callable = None, reverse: bool = False) -> List[Any]:
    """
    排序
    
    Args:
        items: 要排序的列表
        key: 排序键函数
        reverse: 是否降序
        
    Returns:
        排序后的列表
    """
    return sorted(items, key=key, reverse=reverse)


def sort_by(items: List[Any], key: str, reverse: bool = False) -> List[Any]:
    """
    按键排序
    
    Args:
        items: 字典列表
        key: 键名
        reverse: 是否降序
        
    Returns:
        排序后的列表
    """
    return sorted(items, key=lambda x: x.get(key) if isinstance(x, dict) else getattr(x, key, None), reverse=reverse)


def sort_unique(items: List[Any], key: Callable = None) -> List[Any]:
    """
    排序去重
    
    Args:
        items: 要排序的列表
        key: 排序键函数
        
    Returns:
        去重排序后的列表
    """
    seen = set()
    result = []
    
    for item in sorted(items, key=key):
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            result.append(item)
    
    return result


# 导出
__all__ = [
    "SortedList",
    "sort",
    "sort_by",
    "sort_unique",
]
