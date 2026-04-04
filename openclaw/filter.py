"""
Filter - 过滤器
基于 Claude Code filter.ts 设计

数据过滤工具。
"""
from typing import Any, Callable, List, TypeVar

T = TypeVar('T')


def filter_by(items: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    过滤列表
    
    Args:
        items: 列表
        predicate: 过滤函数
        
    Returns:
        过滤后的列表
    """
    return [item for item in items if predicate(item)]


def reject_by(items: List[T], predicate: Callable[[T], bool]) -> List[T]:
    """
    排除列表中满足条件的项
    
    Args:
        items: 列表
        predicate: 排除函数
        
    Returns:
        排除后的列表
    """
    return [item for item in items if not predicate(item)]


def partition_by(
    items: List[T],
    predicate: Callable[[T], bool]
) -> tuple:
    """
    按条件分区
    
    Args:
        items: 列表
        predicate: 条件函数
        
    Returns:
        (满足条件, 不满足条件)
    """
    yes, no = [], []
    for item in items:
        if predicate(item):
            yes.append(item)
        else:
            no.append(item)
    return yes, no


def unique_by(items: List[T], key_fn: Callable[[T], Any]) -> List[T]:
    """
    按键去重
    
    Args:
        items: 列表
        key_fn: 键提取函数
        
    Returns:
        去重后的列表（保留第一个）
    """
    seen = set()
    result = []
    
    for item in items:
        key = key_fn(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def group_by(items: List[T], key_fn: Callable[[T], Any]) -> dict:
    """
    按键分组
    
    Args:
        items: 列表
        key_fn: 键提取函数
        
    Returns:
        {键: [项列表]}
    """
    result = {}
    
    for item in items:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    
    return result


def sort_by(items: List[T], key_fn: Callable[[T], Any], reverse: bool = False) -> List[T]:
    """
    按键排序
    
    Args:
        items: 列表
        key_fn: 键提取函数
        reverse: 是否降序
        
    Returns:
        排序后的列表
    """
    return sorted(items, key=key_fn, reverse=reverse)


def chunk_by(items: List[T], size: int) -> List[List[T]]:
    """
    分块
    
    Args:
        items: 列表
        size: 块大小
        
    Returns:
        分块后的列表
    """
    return [items[i:i+size] for i in range(0, len(items), size)]


def compact(items: List[T]) -> List[T]:
    """
    移除假值
    
    Args:
        items: 列表
        
    Returns:
        移除None/False/''后的列表
    """
    return [item for item in items if item]


# 导出
__all__ = [
    "filter_by",
    "reject_by",
    "partition_by",
    "unique_by",
    "group_by",
    "sort_by",
    "chunk_by",
    "compact",
]
