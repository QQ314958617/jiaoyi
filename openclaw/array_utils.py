"""
Array Utilities - 数组工具
基于 Claude Code array.ts 设计

提供各种数组操作函数。
"""
from typing import Callable, Iterable, TypeVar

A = TypeVar('A')


def intersperse(as: list[A], separator: Callable[[int], A]) -> list[A]:
    """
    在元素之间插入分隔符
    
    Args:
        as: 元素列表
        separator: 分隔符生成函数（接收索引）
        
    Returns:
        插入分隔符后的列表
        
    Example:
        >>> intersperse([1, 2, 3], lambda i: 0)
        [1, 0, 2, 0, 3]
    """
    result = []
    for i, a in enumerate(as):
        if i > 0:
            result.append(separator(i))
        result.append(a)
    return result


def count(arr: list[A], pred: Callable[[A], bool]) -> int:
    """
    计算满足条件的元素数量
    
    Args:
        arr: 数组
        pred: 条件函数
        
    Returns:
        满足条件的元素数量
    """
    return sum(1 for x in arr if pred(x))


def uniq(xs: Iterable[A]) -> list[A]:
    """
    去重（保持顺序）
    
    Args:
        xs: 可迭代对象
        
    Returns:
        去重后的列表
    """
    seen = set()
    result = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def chunk(arr: list[A], size: int) -> list[list[A]]:
    """
    将数组分块
    
    Args:
        arr: 数组
        size: 块大小
        
    Returns:
        分块后的数组
        
    Example:
        >>> chunk([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [arr[i:i+size] for i in range(0, len(arr), size)]


def group_by(arr: list[A], key_fn: Callable[[A], str]) -> dict[str, list[A]]:
    """
    按键分组
    
    Args:
        arr: 数组
        key_fn: 键提取函数
        
    Returns:
        分组后的字典
    """
    result: dict[str, list[A]] = {}
    for item in arr:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def flatten(arr: list) -> list:
    """
    展平嵌套数组
    
    Args:
        arr: 嵌套数组
        
    Returns:
        展平后的数组
    """
    result = []
    for item in arr:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def partition(arr: list[A], pred: Callable[[A], bool]) -> tuple[list[A], list[A]]:
    """
    按条件分区
    
    Args:
        arr: 数组
        pred: 条件函数
        
    Returns:
        (满足条件的, 不满足条件的)
    """
    yes, no = [], []
    for item in arr:
        if pred(item):
            yes.append(item)
        else:
            no.append(item)
    return yes, no


# 导出
__all__ = [
    "intersperse",
    "count",
    "uniq",
    "chunk",
    "group_by",
    "flatten",
    "partition",
]
