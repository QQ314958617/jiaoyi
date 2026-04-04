"""
Omit - 省略
基于 Claude Code omit.ts 设计

对象属性操作工具。
"""
from typing import Any, Callable, Dict, List


def pick(obj: Dict, *keys: str) -> Dict:
    """
    选取属性
    
    Args:
        obj: 字典
        *keys: 要保留的键
        
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


def pick_by(obj: Dict, predicate: Callable) -> Dict:
    """
    按条件选取
    
    Args:
        obj: 字典
        predicate: (key, value) -> bool
        
    Returns:
        新字典
    """
    return {k: v for k, v in obj.items() if predicate(k, v)}


def omit_by(obj: Dict, predicate: Callable) -> Dict:
    """
    按条件排除
    
    Args:
        obj: 字典
        predicate: (key, value) -> bool
        
    Returns:
        新字典
    """
    return {k: v for k, v in obj.items() if not predicate(k, v)}


def rename(obj: Dict, mapping: Dict) -> Dict:
    """
    重命名键
    
    Args:
        obj: 字典
        mapping: {旧键: 新键}
        
    Returns:
        新字典
    """
    result = {}
    for k, v in obj.items():
        new_key = mapping.get(k, k)
        result[new_key] = v
    return result


def deep_pick(obj: Dict, *paths: str) -> Dict:
    """
    深度选取
    
    Args:
        obj: 字典
        *paths: 路径（如 'a.b.c'）
        
    Returns:
        新字典
    """
    result = {}
    
    for path in paths:
        keys = path.split('.')
        value = obj
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = None
                break
        
        if value is not None:
            result[path] = value
    
    return result


def defaults(obj: Dict, defaults: Dict) -> Dict:
    """
    合并默认项
    
    Args:
        obj: 字典
        defaults: 默认字典
        
    Returns:
        合并后的字典
    """
    result = dict(defaults)
    result.update(obj)
    return result


def set_path(obj: Dict, path: str, value: Any) -> Dict:
    """
    设置嵌套值
    
    Args:
        obj: 字典
        path: 路径（如 'a.b.c'）
        value: 值
        
    Returns:
        新字典
    """
    keys = path.split('.')
    result = dict(obj)
    current = result
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        elif not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
    return result


def get_path(obj: Dict, path: str, default: Any = None) -> Any:
    """
    获取嵌套值
    
    Args:
        obj: 字典
        path: 路径
        default: 默认值
        
    Returns:
        值或默认值
    """
    keys = path.split('.')
    value = obj
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


# 导出
__all__ = [
    "pick",
    "omit",
    "pick_by",
    "omit_by",
    "rename",
    "deep_pick",
    "defaults",
    "set_path",
    "get_path",
]
