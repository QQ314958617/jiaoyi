"""
Object - 对象
基于 Claude Code object.ts 设计

对象工具。
"""
from typing import Any, Callable, Dict, List


def pick(obj: Dict, *keys: str) -> Dict:
    """
    选取属性
    
    Args:
        obj: 字典
        *keys: 要选取的键
        
    Returns:
        新字典
    """
    return {k: obj[k] for k in keys if k in obj}


def omit(obj: Dict, *keys: str) -> Dict:
    """
    排除属性
    
    Args:
        obj: 字典
        *keys: 要排除的键
        
    Returns:
        新字典
    """
    return {k: v for k, v in obj.items() if k not in keys}


def merge(*dicts: Dict) -> Dict:
    """
    合并对象
    
    Args:
        *dicts: 字典
        
    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def deep_merge(*dicts: Dict) -> Dict:
    """
    深度合并
    
    Args:
        *dicts: 字典
        
    Returns:
        深度合并后的字典
    """
    result = {}
    for d in dicts:
        if d:
            for k, v in d.items():
                if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                    result[k] = deep_merge(result[k], v)
                else:
                    result[k] = v
    return result


def map_values(obj: Dict, fn: Callable) -> Dict:
    """
    映射值
    
    Args:
        obj: 字典
        fn: 映射函数
        
    Returns:
        新字典
    """
    return {k: fn(v) for k, v in obj.items()}


def map_keys(obj: Dict, fn: Callable) -> Dict:
    """
    映射键
    
    Args:
        obj: 字典
        fn: 映射函数
        
    Returns:
        新字典
    """
    return {fn(k): v for k, v in obj.items()}


def filter_keys(obj: Dict, fn: Callable) -> Dict:
    """
    过滤键
    
    Args:
        obj: 字典
        fn: 谓词
        
    Returns:
        过滤后的字典
    """
    return {k: v for k, v in obj.items() if fn(k)}


def filter_values(obj: Dict, fn: Callable) -> Dict:
    """
    过滤值
    
    Args:
        obj: 字典
        fn: 谓词
        
    Returns:
        过滤后的字典
    """
    return {k: v for k, v in obj.items() if fn(v)}


def invert(obj: Dict) -> Dict:
    """
    反转键值
    
    Args:
        obj: 字典
        
    Returns:
        键值互换的字典
    """
    return {v: k for k, v in obj.items()}


def get_path(obj: Dict, path: str, default: Any = None) -> Any:
    """
    获取嵌套值
    
    Args:
        obj: 字典
        path: 路径 (a.b.c)
        default: 默认值
        
    Returns:
        值或默认值
    """
    keys = path.split('.')
    value = obj
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def set_path(obj: Dict, path: str, value: Any) -> Dict:
    """
    设置嵌套值
    
    Args:
        obj: 字典
        path: 路径
        value: 值
        
    Returns:
        新字典
    """
    keys = path.split('.')
    result = dict(obj)
    current = result
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return result


# 导出
__all__ = [
    "pick",
    "omit",
    "merge",
    "deep_merge",
    "map_values",
    "map_keys",
    "filter_keys",
    "filter_values",
    "invert",
    "get_path",
    "set_path",
]
