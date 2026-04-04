"""
Transform2 - 转换工具2
基于 Claude Code transform2.ts 设计

数据转换工具。
"""
from typing import Any, Callable, Dict, List, TypeVar

T = TypeVar('T')
U = TypeVar('U')


def map_list(items: List[T], fn: Callable[[T], U]) -> List[U]:
    """
    映射
    
    Args:
        items: 列表
        fn: 转换函数
        
    Returns:
        转换后的列表
    """
    return [fn(item) for item in items]


def filter_list(items: List[T], fn: Callable[[T], bool]) -> List[T]:
    """
    过滤
    
    Args:
        items: 列表
        fn: 过滤函数
        
    Returns:
        过滤后的列表
    """
    return [item for item in items if fn(item)]


def reduce_list(
    items: List[T],
    fn: Callable[[Any, T], Any],
    initial: Any = None,
) -> Any:
    """
    归约
    
    Args:
        items: 列表
        fn: 归约函数
        initial: 初始值
        
    Returns:
        归约结果
    """
    result = initial
    
    for item in items:
        result = fn(result, item)
    
    return result


def flat_map(items: List[List[T]]) -> List[T]:
    """
    扁平映射
    
    Args:
        items: 嵌套列表
        
    Returns:
        扁平化后的列表
    """
    return [item for sublist in items for item in sublist]


def flatten(items: List[Any]) -> List[Any]:
    """
    扁平化
    
    Args:
        items: 可能嵌套的列表
        
    Returns:
        扁平化后的列表
    """
    result = []
    
    for item in items:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    
    return result


def group_by(items: List[T], key_fn: Callable[[T], Any]) -> Dict[Any, List[T]]:
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


def key_by(items: List[T], key_fn: Callable[[T], Any]) -> Dict[Any, T]:
    """
    以键索引
    
    Args:
        items: 列表
        key_fn: 键函数
        
    Returns:
        键值字典
    """
    return {key_fn(item): item for item in items}


def uniq(items: List[T]) -> List[T]:
    """
    去重（保持顺序）
    
    Args:
        items: 列表
        
    Returns:
        去重后的列表
    """
    seen = set()
    return [x for x in items if not (x in seen or seen.add(x))]


def uniq_by(items: List[T], fn: Callable[[T], Any]) -> List[T]:
    """
    按函数去重
    
    Args:
        items: 列表
        fn: 去重函数
        
    Returns:
        去重后的列表
    """
    seen = set()
    result = []
    
    for item in items:
        key = fn(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def sort_by(items: List[T], key_fn: Callable[[T], Any] = None, reverse: bool = False) -> List[T]:
    """
    排序
    
    Args:
        items: 列表
        key_fn: 排序键函数
        reverse: 是否降序
        
    Returns:
        排序后的列表
    """
    return sorted(items, key=key_fn, reverse=reverse)


def pluck(items: List[dict], key: str) -> List[Any]:
    """
    提取键值
    
    Args:
        items: 字典列表
        key: 键名
        
    Returns:
        值列表
    """
    return [item.get(key) for item in items if isinstance(item, dict)]


def invoke(items: List[T], method: str, *args) -> List[Any]:
    """
    调用方法
    
    Args:
        items: 对象列表
        method: 方法名
        *args: 方法参数
        
    Returns:
        结果列表
    """
    results = []
    
    for item in items:
        if hasattr(item, method):
            result = getattr(item, method)(*args)
            results.append(result)
    
    return results


def tap_list(items: List[T], fn: Callable[[T], None]) -> List[T]:
    """
    逐项执行副作用
    
    Args:
        items: 列表
        fn: 副作用函数
        
    Returns:
        原列表
    """
    for item in items:
        fn(item)
    return items


# 导出
__all__ = [
    "map_list",
    "filter_list",
    "reduce_list",
    "flat_map",
    "flatten",
    "group_by",
    "key_by",
    "uniq",
    "uniq_by",
    "sort_by",
    "pluck",
    "invoke",
    "tap_list",
]
