"""
Merge2 - 合并
基于 Claude Code merge.ts 设计

合并工具。
"""
from typing import Any, Callable, Dict, List


def merge(*dicts: Dict) -> Dict:
    """
    合并字典
    
    Args:
        *dicts: 字典
        
    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def deep_merge(*dicts: Dict) -> Dict:
    """
    深度合并
    
    Args:
        *dicts: 字典
        
    Returns:
        深度合并后的字典
    """
    result = {}
    
    for d in dicts:
        if d:
            for key, value in d.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
    
    return result


def concat(*lists: List) -> List:
    """
    合并列表
    
    Args:
        *lists: 列表
        
    Returns:
        合并后的列表
    """
    result = []
    for lst in lists:
        if lst:
            result.extend(lst)
    return result


def union(*lists: List) -> List:
    """
    并集（去重）
    
    Args:
        *lists: 列表
        
    Returns:
        并集列表
    """
    seen = set()
    result = []
    for lst in lists:
        if lst:
            for item in lst:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
    return result


def intersection(*lists: List) -> List:
    """
    交集
    
    Args:
        *lists: 列表
        
    Returns:
        交集列表
    """
    if not lists:
        return []
    
    result = []
    first_set = set(lists[0])
    
    for item in first_set:
        if all(item in lst for lst in lists[1:]):
            result.append(item)
    
    return result


def difference(base: List, *others: List) -> List:
    """
    差集
    
    Args:
        base: 基础列表
        *others: 其他列表
        
    Returns:
        差集列表
    """
    result = []
    other_set = set()
    
    for other in others:
        other_set.update(other)
    
    for item in base:
        if item not in other_set:
            result.append(item)
    
    return result


def zip_merge(*lists: List) -> List[List]:
    """
    按索引合并
    
    Args:
        *lists: 列表
        
    Returns:
        合并后的列表
    """
    return [list(items) for items in zip(*lists)]


def chunk_merge(lists: List[List], size: int) -> List[List]:
    """
    块合并
    
    Args:
        lists: 列表的列表
        size: 合并大小
        
    Returns:
        合并后的块列表
    """
    result = []
    current = []
    
    for lst in lists:
        current.extend(lst)
        if len(current) >= size:
            result.append(current[:size])
            current = current[size:]
    
    if current:
        result.append(current)
    
    return result


# 导出
__all__ = [
    "merge",
    "deep_merge",
    "concat",
    "union",
    "intersection",
    "difference",
    "zip_merge",
    "chunk_merge",
]
