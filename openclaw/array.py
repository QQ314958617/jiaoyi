"""
Array - 数组
基于 Claude Code array.ts 设计

数组工具。
"""
from typing import Any, Callable, List


def chunk(items: List, size: int) -> List[List]:
    """
    分块
    
    Args:
        items: 列表
        size: 块大小
        
    Returns:
        块列表
    """
    return [items[i:i+size] for i in range(0, len(items), size)]


def flatten(items: List) -> List:
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
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def unique(items: List) -> List:
    """
    去重（保持顺序）
    
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


def compact(items: List) -> List:
    """
    移除假值
    
    Args:
        items: 列表
        
    Returns:
        移除假值后的列表
    """
    return [item for item in items if item]


def group_by(items: List, key_fn: Callable) -> dict:
    """
    分组
    
    Args:
        items: 列表
        key_fn: 键函数
        
    Returns:
        分组字典
    """
    result = {}
    for item in items:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def partition(items: List, predicate: Callable) -> tuple:
    """
    分区
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        (满足, 不满足)
    """
    yes = []
    no = []
    for item in items:
        if predicate(item):
            yes.append(item)
        else:
            no.append(item)
    return yes, no


def take(items: List, n: int) -> List:
    """取前n个"""
    return items[:n]


def skip(items: List, n: int) -> List:
    """跳过前n个"""
    return items[n:]


def first(items: List, n: int = 1) -> Any:
    """第一个或前n个"""
    if n == 1:
        return items[0] if items else None
    return items[:n]


def last(items: List, n: int = 1) -> Any:
    """最后一个或后n个"""
    if n == 1:
        return items[-1] if items else None
    return items[-n:]


def shuffle(items: List) -> List:
    """随机打乱"""
    import random
    result = list(items)
    random.shuffle(result)
    return result


def sample(items: List, n: int = 1) -> List:
    """随机抽样"""
    import random
    return random.sample(items, min(n, len(items)))


# 导出
__all__ = [
    "chunk",
    "flatten",
    "unique",
    "compact",
    "group_by",
    "partition",
    "take",
    "skip",
    "first",
    "last",
    "shuffle",
    "sample",
]
