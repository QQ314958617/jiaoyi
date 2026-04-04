"""
Collection - 集合
基于 Claude Code collection.ts 设计

集合工具。
"""
from typing import Any, Callable, List, TypeVar

T = TypeVar('T')


def first(items: List[T]) -> T:
    """第一个元素"""
    return items[0] if items else None


def last(items: List[T]) -> T:
    """最后一个元素"""
    return items[-1] if items else None


def rest(items: List[T]) -> List[T]:
    """除第一个外的所有元素"""
    return items[1:] if items else []


def but_last(items: List[T]) -> List[T]:
    """除最后一个外的所有元素"""
    return items[:-1] if items else []


def single(items: List[T]) -> bool:
    """是否只有一个元素"""
    return len(items) == 1


def empty(items: List[T]) -> bool:
    """是否为空"""
    return len(items) == 0


def size(items: List[T]) -> int:
    """元素数量"""
    return len(items)


def find(items: List[T], predicate: Callable) -> T:
    """查找满足条件的第一个元素"""
    for item in items:
        if predicate(item):
            return item
    return None


def filter_items(items: List[T], predicate: Callable) -> List[T]:
    """过滤"""
    return [item for item in items if predicate(item)]


def reject(items: List[T], predicate: Callable) -> List[T]:
    """拒绝满足条件的元素"""
    return [item for item in items if not predicate(item)]


def map_items(items: List[T], fn: Callable) -> List:
    """映射"""
    return [fn(item) for item in items]


def flat_map(items: List[T], fn: Callable) -> List:
    """扁平映射"""
    result = []
    for item in items:
        result.extend(fn(item))
    return result


def reduce_items(items: List[T], fn: Callable, initial: Any = None) -> Any:
    """归约"""
    result = initial
    for item in items:
        result = fn(result, item)
    return result


def some(items: List[T], predicate: Callable) -> bool:
    """是否有任意满足条件的元素"""
    for item in items:
        if predicate(item):
            return True
    return False


def every(items: List[T], predicate: Callable) -> bool:
    """是否所有都满足条件"""
    for item in items:
        if not predicate(item):
            return False
    return True


def none(items: List[T], predicate: Callable) -> bool:
    """是否所有都不满足条件"""
    return not some(items, predicate)


def includes(items: List[T], value: Any) -> bool:
    """是否包含元素"""
    return value in items


def pluck(items: List[dict], key: str) -> List:
    """提取属性值"""
    return [item.get(key) for item in items if isinstance(item, dict)]


def sort_by(items: List[T], key: str) -> List[T]:
    """按键排序"""
    return sorted(items, key=lambda x: x.get(key) if isinstance(x, dict) else getattr(x, key, None))


# 导出
__all__ = [
    "first",
    "last",
    "rest",
    "but_last",
    "single",
    "empty",
    "size",
    "find",
    "filter_items",
    "reject",
    "map_items",
    "flat_map",
    "reduce_items",
    "some",
    "every",
    "none",
    "includes",
    "pluck",
    "sort_by",
]
