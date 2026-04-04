"""
List2 - 列表
基于 Claude Code list.ts 设计

列表工具。
"""
from typing import Any, Callable, List


def unique(items: List) -> List:
    """
    去重
    
    Args:
        items: 列表
        
    Returns:
        去重列表（保持顺序）
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def unique_by(items: List, key_fn: Callable) -> List:
    """
    按键去重
    
    Args:
        items: 列表
        key_fn: 键函数
        
    Returns:
        去重列表
    """
    seen = set()
    result = []
    for item in items:
        key = key_fn(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def flatten(items: List, depth: int = None) -> List:
    """
    扁平化
    
    Args:
        items: 列表
        depth: 深度（None无限）
        
    Returns:
        扁平化列表
    """
    result = []
    
    for item in items:
        if isinstance(item, list):
            if depth is None or depth > 0:
                result.extend(flatten(item, None if depth is None else depth - 1))
            else:
                result.append(item)
        else:
            result.append(item)
    
    return result


def chunk(items: List, size: int) -> List[List]:
    """
    分块
    
    Args:
        items: 列表
        size: 块大小
        
    Returns:
        块列表
    """
    return [items[i:i + size] for i in range(0, len(items), size)]


def partition(items: List, predicate: Callable) -> tuple:
    """
    分区
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        (满足条件, 不满足)
    """
    yes = []
    no = []
    for item in items:
        if predicate(item):
            yes.append(item)
        else:
            no.append(item)
    return yes, no


def compact(items: List) -> List:
    """
    移除假值
    
    Args:
        items: 列表
        
    Returns:
        移除假值后的列表
    """
    return [item for item in items if item]


def zip_longest(*lists, fillvalue=None) -> List[List]:
    """
    拉链（不等长填充）
    
    Args:
        *lists: 列表
        fillvalue: 填充值
        
    Returns:
        合并后的列表
    """
    max_len = max(len(l) for l in lists)
    result = []
    for i in range(max_len):
        row = []
        for l in lists:
            row.append(l[i] if i < len(l) else fillvalue)
        result.append(row)
    return result


def difference(items: List, *others) -> List:
    """
    差集
    
    Args:
        items: 列表
        *others: 其他列表
        
    Returns:
        在items但不在others的元素
    """
    result = []
    all_others = set()
    for other in others:
        all_others.update(other)
    for item in items:
        if item not in all_others:
            result.append(item)
    return result


def intersection(items: List, *others) -> List:
    """
    交集
    
    Args:
        items: 列表
        *others: 其他列表
        
    Returns:
        在所有列表中都存在的元素
    """
    if not others:
        return list(items)
    result = []
    sets = [set(other) for other in others]
    for item in items:
        if all(item in s for s in sets):
            result.append(item)
    return result


# 导出
__all__ = [
    "unique",
    "unique_by",
    "flatten",
    "chunk",
    "partition",
    "compact",
    "zip_longest",
    "difference",
    "intersection",
]
