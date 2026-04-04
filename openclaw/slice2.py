"""
Slice2 - 切片
基于 Claude Code slice.ts 设计

切片工具。
"""
from typing import Any, List, Iterable


def slice(items: List, start: int = None, end: int = None) -> List:
    """
    切片
    
    Args:
        items: 列表
        start: 起始索引
        end: 结束索引
        
    Returns:
        切片后的列表
    """
    return items[start:end]


def first(items: List, n: int = 1) -> List:
    """
    获取前n个元素
    
    Args:
        items: 列表
        n: 数量
        
    Returns:
        前n个元素
    """
    return items[:n]


def last(items: List, n: int = 1) -> List:
    """
    获取后n个元素
    
    Args:
        items: 列表
        n: 数量
        
    Returns:
        后n个元素
    """
    return items[-n:] if n > 0 else []


def initial(items: List) -> List:
    """
    获取除最后一个外的所有元素
    
    Args:
        items: 列表
        
    Returns:
        除最后一个外的列表
    """
    return items[:-1]


def tail(items: List) -> List:
    """
    获取除第一个外的所有元素
    
    Args:
        items: 列表
        
    Returns:
        除第一个外的列表
    """
    return items[1:]


def take(items: List, n: int) -> List:
    """
    取前n个
    
    Args:
        items: 列表
        n: 数量
        
    Returns:
        前n个
    """
    return items[:n]


def skip(items: List, n: int) -> List:
    """
    跳过前n个
    
    Args:
        items: 列表
        n: 数量
        
    Returns:
        跳过后的列表
    """
    return items[n:]


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


def partition(items: List, predicate) -> tuple:
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


def split_at(items: List, index: int) -> tuple:
    """
    在索引处分割
    
    Args:
        items: 列表
        index: 索引
        
    Returns:
        (前半, 后半)
    """
    return items[:index], items[index:]


def split_every(items: List, size: int) -> List[List]:
    """
    每n个分割
    
    Args:
        items: 列表
        size: 大小
        
    Returns:
        分割后的列表
    """
    return chunk(items, size)


# 导出
__all__ = [
    "slice",
    "first",
    "last",
    "initial",
    "tail",
    "take",
    "skip",
    "chunk",
    "partition",
    "split_at",
    "split_every",
]
