"""
Values - 值
基于 Claude Code values.ts 设计

值工具。
"""
from typing import Any, Callable, Dict, List


def values(obj: Dict) -> List:
    """获取所有值"""
    return list(obj.values())


def unique_values(items: List) -> List:
    """
    获取唯一值
    
    Args:
        items: 列表
        
    Returns:
        去重列表
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def count_values(items: List) -> Dict[Any, int]:
    """
    统计值出现次数
    
    Args:
        items: 列表
        
    Returns:
        {值: 次数}
    """
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


def group_by_value(items: List) -> Dict[Any, List]:
    """
    按值分组
    
    Args:
        items: 列表
        
    Returns:
        {值: [items]}
    """
    groups = {}
    for item in items:
        if item not in groups:
            groups[item] = []
        groups[item].append(item)
    return groups


def filter_values(items: List, predicate: Callable) -> List:
    """
    过滤值
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        过滤后的列表
    """
    return [item for item in items if predicate(item)]


def map_values(items: List, fn: Callable) -> List:
    """
    映射值
    
    Args:
        items: 列表
        fn: 映射函数
        
    Returns:
        映射后的列表
    """
    return [fn(item) for item in items]


def sort_values(items: List, reverse: bool = False) -> List:
    """
    排序值
    
    Args:
        items: 列表
        reverse: 是否降序
        
    Returns:
        排序后的列表
    """
    return sorted(items, reverse=reverse)


def flatten_values(items: List) -> List:
    """
    扁平化
    
    Args:
        items: 嵌套列表
        
    Returns:
        扁平化列表
    """
    result = []
    for item in items:
        if isinstance(item, (list, tuple)):
            result.extend(item)
        else:
            result.append(item)
    return result


def chunk_values(items: List, size: int) -> List[List]:
    """
    分块
    
    Args:
        items: 列表
        size: 块大小
        
    Returns:
        块列表
    """
    return [items[i:i+size] for i in range(0, len(items), size)]


def compact_values(items: List) -> List:
    """
    移除假值
    
    Args:
        items: 列表
        
    Returns:
        移除假值后的列表
    """
    return [item for item in items if item]


def zip_values(*lists: List) -> List[List]:
    """
    拉链
    
    Args:
        *lists: 列表
        
    Returns:
        合并列表
    """
    return [list(items) for items in zip(*lists)]


# 导出
__all__ = [
    "values",
    "unique_values",
    "count_values",
    "group_by_value",
    "filter_values",
    "map_values",
    "sort_values",
    "flatten_values",
    "chunk_values",
    "compact_values",
    "zip_values",
]
