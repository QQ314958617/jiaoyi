"""
Iter - 迭代器
基于 Claude Code iter.ts 设计

迭代器工具。
"""
from typing import Any, Callable, Iterable, Iterator, List, Optional


def iterator(source: Iterable) -> Iterator:
    """获取迭代器"""
    return iter(source)


def next_item(iterator: Iterator, default: Any = None) -> Any:
    """获取下一个元素"""
    try:
        return next(iterator)
    except StopIteration:
        return default


def for_each(items: Iterable, fn: Callable) -> None:
    """遍历"""
    for item in items:
        fn(item)


def filter_items(items: Iterable, predicate: Callable) -> list:
    """过滤"""
    return [item for item in items if predicate(item)]


def map_items(items: Iterable, fn: Callable) -> list:
    """映射"""
    return [fn(item) for item in items]


def reduce_items(items: Iterable, fn: Callable, initial: Any = None) -> Any:
    """归约"""
    result = initial
    for item in items:
        result = fn(result, item)
    return result


def find_item(items: Iterable, predicate: Callable) -> Optional[Any]:
    """查找"""
    for item in items:
        if predicate(item):
            return item
    return None


def find_index(items: Iterable, predicate: Callable) -> int:
    """查找索引"""
    for i, item in enumerate(items):
        if predicate(item):
            return i
    return -1


def any_match(items: Iterable, predicate: Callable) -> bool:
    """是否有匹配"""
    for item in items:
        if predicate(item):
            return True
    return False


def all_match(items: Iterable, predicate: Callable) -> bool:
    """是否全部匹配"""
    for item in items:
        if not predicate(item):
            return False
    return True


def none_match(items: Iterable, predicate: Callable) -> bool:
    """是否都不匹配"""
    return not any_match(items, predicate)


def take(items: Iterable, n: int) -> list:
    """取前n个"""
    result = []
    for i, item in enumerate(items):
        if i < n:
            result.append(item)
        else:
            break
    return result


def skip(items: Iterable, n: int) -> list:
    """跳过前n个"""
    result = []
    for i, item in enumerate(items):
        if i >= n:
            result.append(item)
    return result


def chunk(items: Iterable, size: int) -> list:
    """分块"""
    result = []
    current = []
    for i, item in enumerate(items):
        current.append(item)
        if len(current) >= size:
            result.append(current)
            current = []
    if current:
        result.append(current)
    return result


def flatten(items: Iterable) -> list:
    """扁平化"""
    result = []
    for item in items:
        if isinstance(item, (list, tuple)):
            result.extend(item)
        else:
            result.append(item)
    return result


def unique(items: Iterable) -> list:
    """去重"""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def zip_items(*iterables) -> list:
    """拉链"""
    return [list(items) for items in zip(*iterables)]


def enumerate_items(items: Iterable) -> list:
    """枚举"""
    return list(enumerate(items))


class Iter:
    """
    迭代器链
    """
    
    def __init__(self, source: Iterable):
        self._items = list(source)
        self._index = 0
    
    def filter(self, predicate: Callable) -> "Iter":
        self._items = [x for x in self._items if predicate(x)]
        return self
    
    def map(self, fn: Callable) -> "Iter":
        self._items = [fn(x) for x in self._items]
        return self
    
    def take(self, n: int) -> "Iter":
        self._items = self._items[:n]
        return self
    
    def skip(self, n: int) -> "Iter":
        self._items = self._items[n:]
        return self
    
    def unique(self) -> "Iter":
        seen = set()
        result = []
        for item in self._items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        self._items = result
        return self
    
    def collect(self) -> list:
        return list(self._items)
    
    def __iter__(self):
        return iter(self._items)


# 导出
__all__ = [
    "iterator",
    "next_item",
    "for_each",
    "filter_items",
    "map_items",
    "reduce_items",
    "find_item",
    "find_index",
    "any_match",
    "all_match",
    "none_match",
    "take",
    "skip",
    "chunk",
    "flatten",
    "unique",
    "zip_items",
    "enumerate_items",
    "Iter",
]
