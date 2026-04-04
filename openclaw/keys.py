"""
Keys - 键
基于 Claude Code keys.ts 设计

键工具。
"""
from typing import Any, Callable, Dict, Iterable, List


def keys(obj: Dict) -> List:
    """
    获取所有键
    
    Args:
        obj: 对象
        
    Returns:
        键列表
    """
    return list(obj.keys())


def values(obj: Dict) -> List:
    """
    获取所有值
    
    Args:
        obj: 对象
        
    Returns:
        值列表
    """
    return list(obj.values())


def items(obj: Dict) -> List:
    """
    获取所有键值对
    
    Args:
        obj: 对象
        
    Returns:
        键值对列表
    """
    return list(obj.items())


def map_keys(obj: Dict, fn: Callable) -> Dict:
    """
    映射键
    
    Args:
        obj: 对象
        fn: 键映射函数
        
    Returns:
        新对象
    """
    return {fn(k): v for k, v in obj.items()}


def map_values(obj: Dict, fn: Callable) -> Dict:
    """
    映射值
    
    Args:
        obj: 对象
        fn: 值映射函数
        
    Returns:
        新对象
    """
    return {k: fn(v) for k, v in obj.items()}


def filter_keys(obj: Dict, fn: Callable) -> Dict:
    """
    过滤键
    
    Args:
        obj: 对象
        fn: 谓词 (key) -> bool
        
    Returns:
        过滤后的对象
    """
    return {k: v for k, v in obj.items() if fn(k)}


def filter_values(obj: Dict, fn: Callable) -> Dict:
    """
    过滤值
    
    Args:
        obj: 对象
        fn: 谓词 (value) -> bool
        
    Returns:
        过滤后的对象
    """
    return {k: v for k, v in obj.items() if fn(v)}


def invert(obj: Dict) -> Dict:
    """
    反转键值
    
    Args:
        obj: 对象
        
    Returns:
        键值互换的对象
    """
    return {v: k for k, v in obj.items()}


def pick(obj: Dict, *keys: str) -> Dict:
    """
    选取键
    
    Args:
        obj: 对象
        *keys: 要选取的键
        
    Returns:
        新对象
    """
    return {k: obj[k] for k in keys if k in obj}


def omit(obj: Dict, *keys: str) -> Dict:
    """
    排除键
    
    Args:
        obj: 对象
        *keys: 要排除的键
        
    Returns:
        新对象
    """
    return {k: v for k, v in obj.items() if k not in keys}


def has_key(obj: Dict, key: str) -> bool:
    """检查键是否存在"""
    return key in obj


def get_value(obj: Dict, key: str, default: Any = None) -> Any:
    """获取值"""
    return obj.get(key, default)


def set_value(obj: Dict, key: str, value: Any) -> Dict:
    """设置值"""
    result = dict(obj)
    result[key] = value
    return result


def delete_key(obj: Dict, key: str) -> Dict:
    """删除键"""
    result = dict(obj)
    result.pop(key, None)
    return result


# 导出
__all__ = [
    "keys",
    "values",
    "items",
    "map_keys",
    "map_values",
    "filter_keys",
    "filter_values",
    "invert",
    "pick",
    "omit",
    "has_key",
    "get_value",
    "set_value",
    "delete_key",
]
