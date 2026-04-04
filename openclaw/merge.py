"""
Merge - 合并工具
基于 Claude Code merge.ts 设计

数据合并工具。
"""
from typing import Any, Dict, List


def merge_dict(base: dict, *updates: dict) -> dict:
    """
    深度合并字典
    
    Args:
        base: 基础字典
        *updates: 更新的字典
        
    Returns:
        合并后的字典
    """
    result = dict(base)
    
    for update in updates:
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dict(result[key], value)
            else:
                result[key] = value
    
    return result


def merge_list(list1: List[Any], list2: List[Any], unique: bool = True) -> List[Any]:
    """
    合并列表
    
    Args:
        list1: 第一个列表
        list2: 第二个列表
        unique: 是否去重
        
    Returns:
        合并后的列表
    """
    result = list(list1) + list(list2)
    
    if unique:
        # 保持顺序的去重
        seen = set()
        return [x for x in result if not (x in seen or seen.add(x))]
    
    return result


def merge(*objects: Any) -> Any:
    """
    智能合并
    
    Args:
        *objects: 要合并的对象
        
    Returns:
        合并后的对象
    """
    if not objects:
        return None
    
    # 确定类型
    first = objects[0]
    
    if isinstance(first, dict):
        return merge_dict(*objects)
    elif isinstance(first, list):
        return merge_list(*objects)
    else:
        # 非字典/列表，返回最后一个
        return objects[-1]


def pick_merge(obj: dict, keys: List[str]) -> dict:
    """
    选择性合并
    
    Args:
        obj: 字典
        keys: 要合并的键列表
        
    Returns:
        合并后的字典
    """
    result = {}
    
    for key in keys:
        if key in obj:
            result[key] = obj[key]
    
    return result


def deep_patch(base: dict, patch: dict) -> dict:
    """
    深度补丁
    
    Args:
        base: 基础对象
        patch: 补丁对象
        
    Returns:
        打补丁后的对象
    """
    result = dict(base)
    
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_patch(result[key], value)
        else:
            result[key] = value
    
    return result


def overlay(base: dict, overlay: dict) -> dict:
    """
    覆盖合并
    
    只用overlay中的非None值覆盖base。
    
    Args:
        base: 基础字典
        overlay: 覆盖字典
        
    Returns:
        合并后的字典
    """
    result = dict(base)
    
    for key, value in overlay.items():
        if value is not None:
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = overlay(result[key], value)
            else:
                result[key] = value
    
    return result


# 导出
__all__ = [
    "merge_dict",
    "merge_list",
    "merge",
    "pick_merge",
    "deep_patch",
    "overlay",
]
