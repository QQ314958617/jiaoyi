"""
Sort - 排序
基于 Claude Code sort.ts 设计

排序工具。
"""
from typing import Any, Callable, List


def sort(items: List, key: Callable = None, reverse: bool = False) -> List:
    """
    排序
    
    Args:
        items: 列表
        key: 排序键函数
        reverse: 是否降序
        
    Returns:
        排序后的列表（不修改原列表）
    """
    return sorted(items, key=key, reverse=reverse)


def sort_by(items: List[dict], path: str, reverse: bool = False) -> List:
    """
    按路径排序
    
    Args:
        items: 字典列表
        path: 路径（如 'a.b.c'）
        reverse: 是否降序
        
    Returns:
        排序后的列表
    """
    def get_nested(item, path):
        keys = path.split('.')
        value = item
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None
        return value
    
    return sorted(items, key=lambda x: get_nested(x, path), reverse=reverse)


def sort_with comparator(items: List, comparator: Callable) -> List:
    """
    使用比较器排序
    
    Args:
        items: 列表
        comparator: 比较函数 (a, b) -> int
        
    Returns:
        排序后的列表
    """
    return sorted(items, key=lambda x: x, reverse=False)


def is_sorted(items: List, key: Callable = None) -> bool:
    """
    检查是否已排序
    
    Args:
        items: 列表
        key: 键函数
        
    Returns:
        是否已排序
    """
    if len(items) <= 1:
        return True
    
    key_fn = key or (lambda x: x)
    
    for i in range(len(items) - 1):
        if key_fn(items[i]) > key_fn(items[i + 1]):
            return False
    return True


def insertion_sort(items: List, key: Callable = None) -> List:
    """
    插入排序
    
    Args:
        items: 列表
        key: 键函数
        
    Returns:
        排序后的列表
    """
    result = list(items)
    key_fn = key or (lambda x: x)
    
    for i in range(1, len(result)):
        current = result[i]
        j = i - 1
        
        while j >= 0 and key_fn(result[j]) > key_fn(current):
            result[j + 1] = result[j]
            j -= 1
        
        result[j + 1] = current
    
    return result


def quick_sort(items: List, key: Callable = None) -> List:
    """
    快速排序
    
    Args:
        items: 列表
        key: 键函数
        
    Returns:
        排序后的列表
    """
    if len(items) <= 1:
        return list(items)
    
    key_fn = key or (lambda x: x)
    pivot = items[len(items) // 2]
    pivot_key = key_fn(pivot)
    
    left = [x for x in items if key_fn(x) < pivot_key]
    middle = [x for x in items if key_fn(x) == pivot_key]
    right = [x for x in items if key_fn(x) > pivot_key]
    
    return quick_sort(left, key) + middle + quick_sort(right, key)


# 导出
__all__ = [
    "sort",
    "sort_by",
    "sort_with",
    "is_sorted",
    "insertion_sort",
    "quick_sort",
]
