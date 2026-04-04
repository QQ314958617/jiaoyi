"""
Assign - 赋值
基于 Claude Code assign.ts 设计

对象赋值工具。
"""
from typing import Any, Dict


def assign(target: Dict, *sources: Dict) -> Dict:
    """
    合并对象
    
    Args:
        target: 目标对象
        *sources: 源对象
        
    Returns:
        合并后的目标对象
    """
    result = dict(target)
    
    for source in sources:
        if source:
            result.update(source)
    
    return result


def deep_assign(target: Dict, *sources: Dict) -> Dict:
    """
    深度合并
    
    Args:
        target: 目标对象
        *sources: 源对象
        
    Returns:
        合并后的目标对象
    """
    result = dict(target)
    
    for source in sources:
        if source:
            for key, value in source.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_assign(result[key], value)
                else:
                    result[key] = value
    
    return result


def defaults(target: Dict, default_values: Dict) -> Dict:
    """
    设置默认值
    
    Args:
        target: 目标对象
        default_values: 默认值
        
    Returns:
        目标对象（被修改）
    """
    for key, value in default_values.items():
        if key not in target:
            target[key] = value
    return target


def override(target: Dict, overrides: Dict) -> Dict:
    """
    覆盖值
    
    Args:
        target: 目标对象
        overrides: 覆盖值
        
    Returns:
        目标对象（被修改）
    """
    target.update(overrides)
    return target


def pick_assign(target: Dict, source: Dict, *keys: str) -> Dict:
    """
    选择性赋值
    
    Args:
        target: 目标对象
        source: 源对象
        *keys: 要复制的键
        
    Returns:
        目标对象（被修改）
    """
    for key in keys:
        if key in source:
            target[key] = source[key]
    return target


def omit_assign(target: Dict, source: Dict, *keys: str) -> Dict:
    """
    排除性赋值
    
    Args:
        target: 目标对象
        source: 源对象
        *keys: 要排除的键
        
    Returns:
        目标对象（被修改）
    """
    omit = set(keys)
    for key, value in source.items():
        if key not in omit:
            target[key] = value
    return target


# 导出
__all__ = [
    "assign",
    "deep_assign",
    "defaults",
    "override",
    "pick_assign",
    "omit_assign",
]
