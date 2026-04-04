"""
Slice - 切片工具
基于 Claude Code slice.ts 设计

切片和范围工具。
"""
from typing import Any, List, Sequence, TypeVar

T = TypeVar('T')


def slice_list(items: List[T], start: int = 0, end: int = None) -> List[T]:
    """
    切片列表
    
    Args:
        items: 列表
        start: 起始索引
        end: 结束索引
        
    Returns:
        切片后的列表
    """
    return items[start:end]


def first(items: List[T], n: int = 1) -> List[T]:
    """
    获取前n个元素
    
    Args:
        items: 列表
        n: 数量
        
    Returns:
        前n个元素
    """
    return items[:n]


def last(items: List[T], n: int = 1) -> List[T]:
    """
    获取后n个元素
    
    Args:
        items: 列表
        n: 数量
        
    Returns:
        后n个元素
    """
    return items[-n:] if n > 0 else []


def initial(items: List[T]) -> List[T]:
    """获取除最后一个外的所有元素"""
    return items[:-1]


def tail(items: List[T]) -> List[T]:
    """获取除第一个外的所有元素"""
    return items[1:]


def take(items: List[T], n: int) -> List[T]:
    """take的别名"""
    return first(items, n)


def drop(items: List[T], n: int) -> List[T]:
    """
    跳过前n个元素
    
    Args:
        items: 列表
        n: 跳过的数量
        
    Returns:
        剩余元素
    """
    return items[n:] if n > 0 else items


def take_right(items: List[T], n: int) -> List[T]:
    """从右边取n个"""
    return last(items, n)


def drop_right(items: List[T], n: int) -> List[T]:
    """丢弃右边n个"""
    return items[:-n] if n > 0 else items


def take_while(items: List[T], predicate) -> List[T]:
    """
    连续获取满足条件的元素
    
    Args:
        items: 列表
        predicate: 条件函数
        
    Returns:
        满足条件的连续元素
    """
    result = []
    for item in items:
        if predicate(item):
            result.append(item)
        else:
            break
    return result


def drop_while(items: List[T], predicate) -> List[T]:
    """
    跳过满足条件的连续元素
    
    Args:
        items: 列表
        predicate: 条件函数
        
    Returns:
        跳过后的剩余元素
    """
    result = []
    dropping = True
    
    for item in items:
        if dropping and predicate(item):
            continue
        dropping = False
        result.append(item)
    
    return result


def split_at(items: List[T], index: int) -> tuple:
    """
    在指定索引分割
    
    Args:
        items: 列表
        index: 索引
        
    Returns:
        (前半部分, 后半部分)
    """
    return items[:index], items[index:]


def split_every(items: List[T], size: int) -> List[List[T]]:
    """
    按大小分割
    
    Args:
        items: 列表
        size: 每段大小
        
    Returns:
        分割后的列表
    """
    return [items[i:i+size] for i in range(0, len(items), size)]


def range(start: int, end: int = None, step: int = 1) -> List[int]:
    """
    生成整数序列
    
    Args:
        start: 起始值
        end: 结束值（不含）
        step: 步长
        
    Returns:
        整数列表
    """
    if end is None:
        end = start
        start = 0
    
    return list(range(start, end, step))


def pad_start(items: List[T], length: int, fill_value: T = None) -> List[T]:
    """
    头部填充
    
    Args:
        items: 列表
        length: 目标长度
        fill_value: 填充值
        
    Returns:
        填充后的列表
    """
    if len(items) >= length:
        return items
    
    return [fill_value] * (length - len(items)) + items


def pad_end(items: List[T], length: int, fill_value: T = None) -> List[T]:
    """
    尾部填充
    
    Args:
        items: 列表
        length: 目标长度
        fill_value: 填充值
        
    Returns:
        填充后的列表
    """
    if len(items) >= length:
        return items
    
    return items + [fill_value] * (length - len(items))


# 导出
__all__ = [
    "slice_list",
    "first",
    "last",
    "initial",
    "tail",
    "take",
    "drop",
    "take_right",
    "drop_right",
    "take_while",
    "drop_while",
    "split_at",
    "split_every",
    "range",
    "pad_start",
    "pad_end",
]
