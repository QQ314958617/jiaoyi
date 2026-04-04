"""
Group - 分组
基于 Claude Code group.ts 设计

分组工具。
"""
from typing import Any, Callable, Dict, Iterable, List


def group_by(items: List, key_fn: Callable) -> Dict[Any, List]:
    """
    按键分组
    
    Args:
        items: 列表
        key_fn: 键函数
        
    Returns:
        { key: [items] }
    """
    result: Dict[Any, List] = {}
    
    for item in items:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    
    return result


def group_by_str(items: List, key: str) -> Dict[str, List]:
    """
    按字符串键分组
    
    Args:
        items: 字典列表
        key: 键名
        
    Returns:
        分组结果
    """
    result: Dict[str, List] = {}
    
    for item in items:
        if isinstance(item, dict):
            item_key = item.get(key)
            if item_key not in result:
                result[item_key] = []
            result[item_key].append(item)
    
    return result


def partition(items: List, predicate: Callable) -> tuple:
    """
    分区
    
    Args:
        items: 列表
        predicate: 谓词函数
        
    Returns:
        (满足条件, 不满足条件)
    """
    true_items = []
    false_items = []
    
    for item in items:
        if predicate(item):
            true_items.append(item)
        else:
            false_items.append(item)
    
    return true_items, false_items


def chunk_by(items: List, predicate: Callable) -> List[List]:
    """
    按条件分块
    
    Args:
        items: 列表
        predicate: 谓词（连续相同则同块）
        
    Returns:
        块列表
    """
    if not items:
        return []
    
    result = [[items[0]]]
    current_key = predicate(items[0])
    
    for item in items[1:]:
        key = predicate(item)
        if key == current_key:
            result[-1].append(item)
        else:
            result.append([item])
            current_key = key
    
    return result


def count_by(items: List, key_fn: Callable) -> Dict[Any, int]:
    """
    按键计数
    
    Args:
        items: 列表
        key_fn: 键函数
        
    Returns:
        { key: count }
    """
    result: Dict[Any, int] = {}
    
    for item in items:
        key = key_fn(item)
        result[key] = result.get(key, 0) + 1
    
    return result


# 导出
__all__ = [
    "group_by",
    "group_by_str",
    "partition",
    "chunk_by",
    "count_by",
]
