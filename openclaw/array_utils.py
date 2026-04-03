"""
OpenClaw Array Utilities
=====================
Inspired by Claude Code's src/utils/array.ts.

数组工具，支持：
1. 交集/差集/并集
2. 分组/分区
3. 扁平化
4. 去重
5. 交替合并
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Iterator, List, TypeVar, Optional

T = TypeVar('T')
U = TypeVar('U')

# ============================================================================
# 基础操作
# ============================================================================

def intersperse(items: List[T], separator: T) -> List[T]:
    """
    在元素之间插入分隔符
    
    Example:
        intersperse([1, 2, 3], 0) → [1, 0, 2, 0, 3]
    """
    result = []
    for i, item in enumerate(items):
        if i > 0:
            result.append(separator)
        result.append(item)
    return result

def count(items: List[T], pred: Callable[[T], bool]) -> int:
    """
    计算满足条件的元素数量
    
    Example:
        count([1, 2, 3, 4], lambda x: x % 2 == 0) → 2
    """
    return sum(1 for item in items if pred(item))

def uniq(items: Iterable[T]) -> List[T]:
    """
    去重（保持顺序）
    
    Example:
        uniq([1, 2, 1, 3, 2]) → [1, 2, 3]
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def chunk(items: List[T], size: int) -> List[List[T]]:
    """
    分块
    
    Example:
        chunk([1, 2, 3, 4, 5], 2) → [[1, 2], [3, 4], [5]]
    """
    return [items[i:i + size] for i in range(0, len(items), size)]

def partition(items: List[T], pred: Callable[[T], bool]) -> tuple[List[T], List[T]]:
    """
    分区（满足条件/不满足）
    
    Example:
        partition([1, 2, 3, 4], lambda x: x % 2 == 0) → ([2, 4], [1, 3])
    """
    yes, no = [], []
    for item in items:
        if pred(item):
            yes.append(item)
        else:
            no.append(item)
    return yes, no

def group_by(items: List[T], key_func: Callable[[T], U]) -> dict[U, List[T]]:
    """
    按键分组
    
    Example:
        group_by(['a', 'b', 'AB'], lambda x: len(x)) → {1: ['a', 'b'], 2: ['AB']}
    """
    result = {}
    for item in items:
        key = key_func(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result

def flatten(items: List[Any]) -> List[Any]:
    """
    扁平化（一层）
    
    Example:
        flatten([[1, 2], [3, 4]]) → [1, 2, 3, 4]
    """
    result = []
    for item in items:
        if isinstance(item, list):
            result.extend(item)
        else:
            result.append(item)
    return result

def flat_map(items: List[T], func: Callable[[T], List[U]]) -> List[U]:
    """
    先映射再扁平化
    
    Example:
        flat_map([1, 2], lambda x: [x, x*2]) → [1, 2, 2, 4]
    """
    return flatten([func(item) for item in items])

# ============================================================================
# 集合操作
# ============================================================================

def intersection(a: List[T], b: List[T]) -> List[T]:
    """
    交集
    
    Example:
        intersection([1, 2, 3], [2, 3, 4]) → [2, 3]
    """
    return uniq([x for x in a if x in b])

def difference(a: List[T], b: List[T]) -> List[T]:
    """
    差集（在a中但不在b中）
    
    Example:
        difference([1, 2, 3], [2, 3, 4]) → [1]
    """
    b_set = set(b)
    return [x for x in a if x not in b_set]

def union(a: List[T], b: List[T]) -> List[T]:
    """
    并集
    
    Example:
        union([1, 2], [2, 3]) → [1, 2, 3]
    """
    return uniq(a + b)

def symmetric_difference(a: List[T], b: List[T]) -> List[T]:
    """
    对称差集（在a或b中，但不同时在两者中）
    
    Example:
        symmetric_difference([1, 2, 3], [2, 3, 4]) → [1, 4]
    """
    return difference(a, b) + difference(b, a)

# ============================================================================
# 排序和搜索
# ============================================================================

def sort_by(items: List[T], key_func: Callable[[T], Any]) -> List[T]:
    """
    按键排序（稳定排序）
    
    Example:
        sort_by(['abc', 'a', 'ab'], len) → ['a', 'ab', 'abc']
    """
    return sorted(items, key=key_func)

def min_by(items: List[T], key_func: Callable[[T], Any]) -> Optional[T]:
    """
    按键取最小值
    
    Example:
        min_by([{'a': 1}, {'a': 3}, {'a': 2}], lambda x: x['a']) → {'a': 1}
    """
    if not items:
        return None
    return min(items, key=key_func)

def max_by(items: List[T], key_func: Callable[[T], Any]) -> Optional[T]:
    """
    按键取最大值
    """
    if not items:
        return None
    return max(items, key=key_func)

def binary_search(items: List[T], target: T, key_func: Optional[Callable[[T], Any]] = None) -> int:
    """
    二分查找
    
    要求：items 已按 key_func 排序
    
    Returns: 索引，未找到返回 -1
    """
    if not items:
        return -1
    
    key = key_func if key_func else (lambda x: x)
    target_key = key(target)
    
    lo, hi = 0, len(items) - 1
    
    while lo <= hi:
        mid = (lo + hi) // 2
        mid_key = key(items[mid])
        
        if mid_key == target_key:
            return mid
        elif mid_key < target_key:
            lo = mid + 1
        else:
            hi = mid - 1
    
    return -1

# ============================================================================
# 滑动窗口
# ============================================================================

def sliding_window(items: List[T], size: int) -> Iterator[List[T]]:
    """
    滑动窗口
    
    Example:
        list(sliding_window([1, 2, 3, 4], 2)) → [[1, 2], [2, 3], [3, 4]]
    """
    for i in range(len(items) - size + 1):
        yield items[i:i + size]

def pairwise(items: List[T]) -> Iterator[List[T]]:
    """
    相邻对
    
    Example:
        list(pairwise([1, 2, 3, 4])) → [[1, 2], [2, 3], [3, 4]]
    """
    return sliding_window(items, 2)

# ============================================================================
# 转换
# ============================================================================

def map_entries(obj: dict, func: Callable[[Any, Any], tuple]) -> dict:
    """转换字典的键值对"""
    return dict(func(k, v) for k, v in obj.items())

def filter_entries(obj: dict, pred: Callable[[Any, Any], bool]) -> dict:
    """过滤字典的键值对"""
    return {k: v for k, v in obj.items() if pred(k, v)}

def invert_dict(obj: dict) -> dict:
    """反转字典（值变为键）"""
    return {v: k for k, v in obj.items()}

def merge_dicts(*dicts: dict) -> dict:
    """合并多个字典"""
    result = {}
    for d in dicts:
        result.update(d)
    return result
