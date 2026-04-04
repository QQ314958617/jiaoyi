"""
Set2 - 集合
基于 Claude Code set.ts 设计

集合工具。
"""
from typing import Any, FrozenSet, Iterable, List, Set


class Set:
    """
    集合（包装Python内置set）
    """
    
    def __init__(self, items: Iterable = None):
        """
        Args:
            items: 初始项
        """
        self._set = set(items) if items else set()
    
    def add(self, item: Any) -> None:
        """添加"""
        self._set.add(item)
    
    def remove(self, item: Any) -> bool:
        """移除"""
        if item in self._set:
            self._set.remove(item)
            return True
        return False
    
    def has(self, item: Any) -> bool:
        """检查"""
        return item in self._set
    
    def union(self, other: "Set") -> "Set":
        """并集"""
        result = Set(self._set)
        result._set |= other._set
        return result
    
    def intersection(self, other: "Set") -> "Set":
        """交集"""
        result = Set(self._set)
        result._set &= other._set
        return result
    
    def difference(self, other: "Set") -> "Set":
        """差集"""
        result = Set(self._set)
        result._set -= other._set
        return result
    
    def is_subset(self, other: "Set") -> bool:
        """是否为子集"""
        return self._set <= other._set
    
    def is_superset(self, other: "Set") -> bool:
        """是否为超集"""
        return self._set >= other._set
    
    def is_empty(self) -> bool:
        return len(self._set) == 0
    
    def clear(self) -> None:
        self._set.clear()
    
    def size(self) -> int:
        return len(self._set)
    
    def to_list(self) -> List:
        return list(self._set)
    
    def __len__(self) -> int:
        return len(self._set)
    
    def __contains__(self, item) -> bool:
        return item in self._set
    
    def __iter__(self):
        return iter(self._set)
    
    def __and__(self, other):
        return self.intersection(other)
    
    def __or__(self, other):
        return self.union(other)
    
    def __sub__(self, other):
        return self.difference(other)


def union(*sets: Set) -> Set:
    """多集合并集"""
    result = Set()
    for s in sets:
        result._set |= s._set
    return result


def intersection(*sets: Set) -> Set:
    """多集合交集"""
    if not sets:
        return Set()
    result = Set(sets[0]._set)
    for s in sets[1:]:
        result._set &= s._set
    return result


def difference(base: Set, *sets: Set) -> Set:
    """多集合差集"""
    result = Set(base._set)
    for s in sets:
        result._set -= s._set
    return result


def symmetric_difference(s1: Set, s2: Set) -> Set:
    """对称差集"""
    return s1.union(s2).difference(s1.intersection(s2))


# 导出
__all__ = [
    "Set",
    "union",
    "intersection",
    "difference",
    "symmetric_difference",
]
