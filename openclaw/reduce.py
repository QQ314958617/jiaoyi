"""
Reduce - 归约
基于 Claude Code reduce.ts 设计

归约工具。
"""
from typing import Any, Callable, List, Dict


def reduce(items: List, reducer: Callable, initial: Any = None) -> Any:
    """
    归约
    
    Args:
        items: 列表
        reducer: 归约函数 (accumulator, item) -> new_accumulator
        initial: 初始值
        
    Returns:
        归约结果
    """
    accumulator = initial if initial is not None else items[0] if items else None
    
    start_index = 1 if initial is None and items else 0
    
    for item in items[start_index:]:
        accumulator = reducer(accumulator, item)
    
    return accumulator


def reduce_right(items: List, reducer: Callable, initial: Any = None) -> Any:
    """
    从右向左归约
    
    Args:
        items: 列表
        reducer: 归约函数
        initial: 初始值
        
    Returns:
        归约结果
    """
    return reduce(list(reversed(items)), reducer, initial)


def group_by_reduce(items: List, key_fn: Callable, reducer: Callable, initial: Any = None) -> Dict:
    """
    分组归约
    
    Args:
        items: 列表
        key_fn: 键函数
        reducer: 归约函数
        initial: 初始值
        
    Returns:
        { key: result }
    """
    result = {}
    
    for item in items:
        key = key_fn(item)
        if key not in result:
            result[key] = initial if initial is not None else item
        else:
            result[key] = reducer(result[key], item)
    
    return result


def sum(items: List) -> Any:
    """
    求和
    
    Args:
        items: 列表
        
    Returns:
        和
    """
    return reduce(items, lambda a, b: a + b, 0)


def product(items: List) -> Any:
    """
    求积
    
    Args:
        items: 列表
        
    Returns:
        积
    """
    return reduce(items, lambda a, b: a * b, 1)


def min_value(items: List) -> Any:
    """最小值"""
    return reduce(items, lambda a, b: a if a < b else b)


def max_value(items: List) -> Any:
    """最大值"""
    return reduce(items, lambda a, b: a if a > b else b)


def count(items: List) -> int:
    """计数"""
    return len(items)


def average(items: List) -> float:
    """平均值"""
    if not items:
        return 0
    return sum(items) / len(items)


# 导出
__all__ = [
    "reduce",
    "reduce_right",
    "group_by_reduce",
    "sum",
    "product",
    "min_value",
    "max_value",
    "count",
    "average",
]
