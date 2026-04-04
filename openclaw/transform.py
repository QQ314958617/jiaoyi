"""
Transform - 数据转换
基于 Claude Code transform.ts 设计

常用数据转换工具。
"""
from typing import Any, Callable, Dict, List, Optional


def pick(obj: dict, *keys: str) -> dict:
    """
    选取对象的部分字段
    
    Args:
        obj: 对象
        *keys: 要选取的键
        
    Returns:
        新对象
    """
    return {k: obj[k] for k in keys if k in obj}


def omit(obj: dict, *keys: str) -> dict:
    """
    排除对象的部分字段
    
    Args:
        obj: 对象
        *keys: 要排除的键
        
    Returns:
        新对象
    """
    return {k: v for k, v in obj.items() if k not in keys}


def deep_merge(base: dict, *updates: dict) -> dict:
    """
    深度合并字典
    
    Args:
        base: 基础字典
        *updates: 更新的字典
        
    Returns:
        合并后的新字典
    """
    result = dict(base)
    
    for update in updates:
        for key, value in update.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
    
    return result


def map_values(
    obj: dict,
    fn: Callable[[Any, str], Any],
) -> dict:
    """
    对字典的值应用函数
    
    Args:
        obj: 字典
        fn: 函数 (value, key) -> new_value
        
    Returns:
        新的字典
    """
    return {k: fn(v, k) for k, v in obj.items()}


def map_keys(
    obj: dict,
    fn: Callable[[str, Any], str],
) -> dict:
    """
    对字典的键应用函数
    
    Args:
        obj: 字典
        fn: 函数 (key, value) -> new_key
        
    Returns:
        新的字典
    """
    return {fn(k, v): v for k, v in obj.items()}


def filter_values(
    obj: dict,
    fn: Callable[[Any], bool],
) -> dict:
    """
    过滤字典的值
    
    Args:
        obj: 字典
        fn: 过滤函数
        
    Returns:
        过滤后的字典
    """
    return {k: v for k, v in obj.items() if fn(v)}


def group_by(
    items: list,
    key_fn: Callable[[Any], str],
) -> dict:
    """
    按键分组
    
    Args:
        items: 列表
        key_fn: 键提取函数
        
    Returns:
        分组字典
    """
    result: dict = {}
    for item in items:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def flatten(items: list, depth: int = 1) -> list:
    """
    展平嵌套列表
    
    Args:
        items: 嵌套列表
        depth: 展平深度
        
    Returns:
        展平后的列表
    """
    result = []
    for item in items:
        if depth > 0 and isinstance(item, list):
            result.extend(flatten(item, depth - 1))
        else:
            result.append(item)
    return result


def chunk(items: list, size: int) -> list:
    """
    分块
    
    Args:
        items: 列表
        size: 块大小
        
    Returns:
        分块后的列表
    """
    return [items[i:i + size] for i in range(0, len(items), size)]


def unique(items: list) -> list:
    """
    去重（保持顺序）
    
    Args:
        items: 列表
        
    Returns:
        去重后的列表
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def key_by(
    items: list,
    key_fn: Callable[[Any], str],
) -> dict:
    """
    将列表转换为以键索引的字典
    
    Args:
        items: 列表
        key_fn: 键提取函数
        
    Returns:
        索引字典
    """
    return {key_fn(item): item for item in items}


# 导出
__all__ = [
    "pick",
    "omit",
    "deep_merge",
    "map_values",
    "map_keys",
    "filter_values",
    "group_by",
    "flatten",
    "chunk",
    "unique",
    "key_by",
]
