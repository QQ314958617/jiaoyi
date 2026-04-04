"""
KeyPath - 键路径
基于 Claude Code keyPath.ts 设计

访问嵌套字典的键路径工具。
"""
from typing import Any, Optional


def get(data: dict, path: str, default: Any = None) -> Any:
    """
    获取嵌套字典的值
    
    Args:
        data: 字典
        path: 点分隔的路径（如 "a.b.c"）
        default: 默认值
        
    Returns:
        值或默认值
    """
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def set(data: dict, path: str, value: Any) -> None:
    """
    设置嵌套字典的值
    
    Args:
        data: 字典
        path: 点分隔的路径
        value: 要设置的值
    """
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value


def has(data: dict, path: str) -> bool:
    """
    检查路径是否存在
    
    Args:
        data: 字典
        path: 点分隔的路径
        
    Returns:
        是否存在
    """
    return get(data, path, _NOT_FOUND) is not _NOT_FOUND


def delete(data: dict, path: str) -> bool:
    """
    删除嵌套键
    
    Args:
        data: 字典
        path: 点分隔的路径
        
    Returns:
        是否成功删除
    """
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            return False
        current = current[key]
    
    if keys[-1] in current:
        del current[keys[-1]]
        return True
    return False


def paths(data: dict, prefix: str = '') -> list:
    """
    获取所有键路径
    
    Args:
        data: 字典
        prefix: 路径前缀
        
    Returns:
        所有路径列表
    """
    result = []
    
    for key, value in data.items():
        full_path = f"{prefix}.{key}" if prefix else key
        
        if isinstance(value, dict):
            result.extend(paths(value, full_path))
        else:
            result.append(full_path)
    
    return result


_NOT_FOUND = object()


def flatten(data: dict, prefix: str = '', separator: str = '.') -> dict:
    """
    扁平化嵌套字典
    
    Args:
        data: 字典
        prefix: 路径前缀
        separator: 分隔符
        
    Returns:
        扁平字典
    """
    result = {}
    
    for key, value in data.items():
        full_path = f"{prefix}{separator}{key}" if prefix else key
        
        if isinstance(value, dict):
            result.update(flatten(value, full_path, separator))
        else:
            result[full_path] = value
    
    return result


def unflatten(data: dict, separator: str = '.') -> dict:
    """
    反扁平化字典
    
    Args:
        data: 扁平字典
        separator: 分隔符
        
    Returns:
        嵌套字典
    """
    result = {}
    
    for path, value in data.items():
        keys = path.split(separator)
        current = result
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    return result


# 导出
__all__ = [
    "get",
    "set",
    "has",
    "delete",
    "paths",
    "flatten",
    "unflatten",
]
