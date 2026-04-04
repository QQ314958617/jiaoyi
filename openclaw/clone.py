"""
Clone - 克隆
基于 Claude Code clone.ts 设计

深拷贝工具。
"""
import copy
from typing import Any


def deep_clone(obj: Any) -> Any:
    """
    深拷贝
    
    Args:
        obj: 要拷贝的对象
        
    Returns:
        深拷贝副本
    """
    return copy.deepcopy(obj)


def shallow_clone(obj: Any) -> Any:
    """
    浅拷贝
    
    Args:
        obj: 要拷贝的对象
        
    Returns:
        浅拷贝副本
    """
    if isinstance(obj, list):
        return list(obj)
    elif isinstance(obj, dict):
        return dict(obj)
    elif isinstance(obj, set):
        return set(obj)
    elif isinstance(obj, tuple):
        return tuple(obj)
    else:
        return obj


def clone_with(obj: Any, **updates) -> Any:
    """
    带更新的克隆
    
    Args:
        obj: 原始对象
        **updates: 要更新的字段
        
    Returns:
        更新后的副本
    """
    if isinstance(obj, dict):
        result = dict(obj)
        result.update(updates)
        return result
    elif isinstance(obj, list):
        result = list(obj)
        for key, value in updates.items():
            if isinstance(key, int) and 0 <= key < len(result):
                result[key] = value
        return result
    
    # 尝试深拷贝后更新
    result = copy.deepcopy(obj)
    for key, value in updates.items():
        if hasattr(result, key):
            setattr(result, key, value)
    
    return result


def merge(obj1: Any, obj2: Any) -> Any:
    """
    合并对象
    
    Args:
        obj1: 第一个对象
        obj2: 第二个对象
        
    Returns:
        合并后的对象
    """
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        result = dict(obj1)
        result.update(obj2)
        return result
    elif isinstance(obj1, list) and isinstance(obj2, list):
        return obj1 + obj2
    else:
        return obj2


def pick(obj: dict, keys: list) -> dict:
    """
    选取字段
    
    Args:
        obj: 对象
        keys: 要选取的键列表
        
    Returns:
        只包含指定键的新对象
    """
    return {k: v for k, v in obj.items() if k in keys}


def omit(obj: dict, keys: list) -> dict:
    """
    排除字段
    
    Args:
        obj: 对象
        keys: 要排除的键列表
        
    Returns:
        排除指定键的新对象
    """
    return {k: v for k, v in obj.items() if k not in keys}


def freeze(obj: Any) -> Any:
    """
    冻结对象（不可变）
    
    Args:
        obj: 对象
        
    Returns:
        冻结后的对象
    """
    if isinstance(obj, dict):
        return frozenset(obj.items())
    elif isinstance(obj, list):
        return tuple(freeze(item) for item in obj)
    elif isinstance(obj, set):
        return frozenset(obj)
    else:
        return obj


# 导出
__all__ = [
    "deep_clone",
    "shallow_clone",
    "clone_with",
    "merge",
    "pick",
    "omit",
    "freeze",
]
