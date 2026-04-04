"""
Search - 搜索
基于 Claude Code search.ts 设计

搜索工具。
"""
from typing import List, Callable, Any


def linear_search(items: List[Any], target: Any) -> int:
    """
    线性搜索
    
    Returns:
        索引或-1
    """
    for i, item in enumerate(items):
        if item == target:
            return i
    return -1


def binary_search(items: List[Any], target: Any) -> int:
    """
    二分搜索（需已排序）
    
    Returns:
        索引或-1
    """
    left, right = 0, len(items) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if items[mid] == target:
            return mid
        elif items[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1


def search(items: List[Any], predicate: Callable) -> Any:
    """
    条件搜索
    
    Returns:
        第一个匹配项或None
    """
    for item in items:
        if predicate(item):
            return item
    return None


def find_index(items: List[Any], predicate: Callable) -> int:
    """
    条件搜索索引
    
    Returns:
        索引或-1
    """
    for i, item in enumerate(items):
        if predicate(item):
            return i
    return -1


def find_all(items: List[Any], predicate: Callable) -> List[Any]:
    """
    条件搜索全部
    
    Returns:
        所有匹配项
    """
    return [item for item in items if predicate(item)]


def includes(items: List[Any], target: Any) -> bool:
    """是否包含"""
    return target in items


def starts_with(items: List[Any], prefix: List[Any]) -> bool:
    """是否以prefix开头"""
    return items[:len(prefix)] == prefix


def ends_with(items: List[Any], suffix: List[Any]) -> bool:
    """是否以suffix结尾"""
    return items[-len(suffix):] == suffix


# 导出
__all__ = [
    "linear_search",
    "binary_search",
    "search",
    "find_index",
    "find_all",
    "includes",
    "starts_with",
    "ends_with",
]
