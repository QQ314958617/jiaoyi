"""
Search - 搜索
基于 Claude Code search.ts 设计

搜索工具。
"""
from typing import Any, Callable, List, Optional


def linear_search(items: List, target: Any) -> int:
    """
    线性搜索
    
    Args:
        items: 列表
        target: 目标值
        
    Returns:
        索引或-1
    """
    for i, item in enumerate(items):
        if item == target:
            return i
    return -1


def binary_search(items: List, target: Any) -> int:
    """
    二分搜索（需已排序）
    
    Args:
        items: 已排序列表
        target: 目标值
        
    Returns:
        索引或-1
    """
    lo, hi = 0, len(items) - 1
    
    while lo <= hi:
        mid = (lo + hi) // 2
        
        if items[mid] == target:
            return mid
        elif items[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    
    return -1


def binary_search_left(items: List, target: Any) -> int:
    """
    左插入点（二分搜索）
    
    Args:
        items: 已排序列表
        target: 目标值
        
    Returns:
        第一个 >= target 的索引
    """
    lo, hi = 0, len(items)
    
    while lo < hi:
        mid = (lo + hi) // 2
        if items[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    
    return lo


def binary_search_right(items: List, target: Any) -> int:
    """
    右插入点（二分搜索）
    
    Args:
        items: 已排序列表
        target: 目标值
        
    Returns:
        第一个 > target 的索引
    """
    lo, hi = 0, len(items)
    
    while lo < hi:
        mid = (lo + hi) // 2
        if items[mid] <= target:
            lo = mid + 1
        else:
            hi = mid
    
    return lo


def search_sorted(items: List, target: Any, key: Callable = None) -> int:
    """
    在已排序列表中搜索
    
    Args:
        items: 已排序列表
        target: 目标值
        key: 键函数
        
    Returns:
        索引或-1
    """
    if not key:
        return binary_search(items, target)
    
    key_fn = key
    lo, hi = 0, len(items) - 1
    
    while lo <= hi:
        mid = (lo + hi) // 2
        mid_key = key_fn(items[mid])
        
        if mid_key == target:
            return mid
        elif mid_key < target:
            lo = mid + 1
        else:
            hi = mid - 1
    
    return -1


def find_first(items: List, predicate: Callable) -> Optional[Any]:
    """
    找第一个满足条件的元素
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        元素或None
    """
    for item in items:
        if predicate(item):
            return item
    return None


def find_last(items: List, predicate: Callable) -> Optional[Any]:
    """
    找最后一个满足条件的元素
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        元素或None
    """
    result = None
    for item in items:
        if predicate(item):
            result = item
    return result


def find_min(items: List, key: Callable = None) -> Optional[Any]:
    """
    找最小值
    
    Args:
        items: 列表
        key: 键函数
        
    Returns:
        最小元素
    """
    if not items:
        return None
    key_fn = key or (lambda x: x)
    return min(items, key=key_fn)


def find_max(items: List, key: Callable = None) -> Optional[Any]:
    """
    找最大值
    
    Args:
        items: 列表
        key: 键函数
        
    Returns:
        最大元素
    """
    if not items:
        return None
    key_fn = key or (lambda x: x)
    return max(items, key=key_fn)


# 导出
__all__ = [
    "linear_search",
    "binary_search",
    "binary_search_left",
    "binary_search_right",
    "search_sorted",
    "find_first",
    "find_last",
    "find_min",
    "find_max",
]
