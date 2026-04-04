"""
Sort - 排序
基于 Claude Code sort.ts 设计

排序工具。
"""
from typing import List, Callable, Any


def sort(items: List[Any], key: Callable = None, reverse: bool = False) -> List[Any]:
    """
    排序
    
    Args:
        items: 列表
        key: 排序键函数
        reverse: 是否倒序
        
    Returns:
        新列表
    """
    return sorted(items, key=key, reverse=reverse)


def sort_by(items: List[Any], key: str, reverse: bool = False) -> List[Any]:
    """
    按键排序
    
    Args:
        items: 字典列表
        key: 键名
        reverse: 是否倒序
    """
    return sorted(items, key=lambda x: x.get(key) if isinstance(x, dict) else getattr(x, key, None), 
                  reverse=reverse)


def sort_numbers(items: List[float], reverse: bool = False) -> List[float]:
    """数字排序"""
    return sorted(items, reverse=reverse)


def sort_strings(items: List[str], reverse: bool = False) -> List[str]:
    """字符串排序"""
    return sorted(items, key=str.lower, reverse=reverse)


def bubble_sort(items: List[Any], key: Callable = None) -> List[Any]:
    """
    冒泡排序
    """
    result = list(items)
    n = len(result)
    
    for i in range(n):
        for j in range(0, n - i - 1):
            v1 = key(result[j]) if key else result[j]
            v2 = key(result[j + 1]) if key else result[j + 1]
            if v1 > v2:
                result[j], result[j + 1] = result[j + 1], result[j]
    
    return result


def quick_sort(items: List[Any], key: Callable = None) -> List[Any]:
    """
    快速排序
    """
    if len(items) <= 1:
        return list(items)
    
    pivot = items[0]
    pivot_val = key(pivot) if key else pivot
    
    left = []
    right = []
    
    for item in items[1:]:
        val = key(item) if key else item
        if val <= pivot_val:
            left.append(item)
        else:
            right.append(item)
    
    return quick_sort(left, key) + [pivot] + quick_sort(right, key)


# 导出
__all__ = [
    "sort",
    "sort_by",
    "sort_numbers",
    "sort_strings",
    "bubble_sort",
    "quick_sort",
]
