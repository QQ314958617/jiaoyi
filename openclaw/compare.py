"""
Compare - 比较
基于 Claude Code compare.ts 设计

比较工具。
"""
from typing import Any, Callable


def compare(a: Any, b: Any) -> int:
    """
    比较
    
    Args:
        a: 值1
        b: 值2
        
    Returns:
        -1 (a < b), 0 (a == b), 1 (a > b)
    """
    if a < b:
        return -1
    elif a > b:
        return 1
    return 0


def equal(a: Any, b: Any) -> bool:
    """相等"""
    return a == b


def deep_equal(a: Any, b: Any) -> bool:
    """
    深度相等
    
    Args:
        a: 值1
        b: 值2
        
    Returns:
        是否深度相等
    """
    if type(a) != type(b):
        return False
    
    if isinstance(a, dict):
        if len(a) != len(b):
            return False
        for key in a:
            if key not in b or not deep_equal(a[key], b[key]):
                return False
        return True
    
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(deep_equal(av, bv) for av, bv in zip(a, b))
    
    return a == b


def identical(a: Any, b: Any) -> bool:
    """严格相等"""
    return a is b


def greater_than(a: Any, b: Any) -> bool:
    """大于"""
    return a > b


def less_than(a: Any, b: Any) -> bool:
    """小于"""
    return a < b


def between(value: Any, min_val: Any, max_val: Any) -> bool:
    """
    是否在范围内
    
    Args:
        value: 值
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        是否在范围内
    """
    return min_val <= value <= max_val


class Comparator:
    """
    比较器
    """
    
    def __init__(self, key_fn: Callable = None, reverse: bool = False):
        """
        Args:
            key_fn: 键函数
            reverse: 是否反向
        """
        self._key_fn = key_fn or (lambda x: x)
        self._reverse = reverse
    
    def compare(self, a: Any, b: Any) -> int:
        """比较"""
        ka = self._key_fn(a)
        kb = self._key_fn(b)
        
        if ka < kb:
            return -1 if not self._reverse else 1
        if ka > kb:
            return 1 if not self._reverse else -1
        return 0
    
    def __call__(self, a: Any, b: Any) -> int:
        return self.compare(a, b)


# 导出
__all__ = [
    "compare",
    "equal",
    "deep_equal",
    "identical",
    "greater_than",
    "less_than",
    "between",
    "Comparator",
]
