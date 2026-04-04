"""
Clone - 克隆
基于 Claude Code clone.ts 设计

克隆工具。
"""
import copy
from typing import Any, Dict, List


def shallow_clone(obj: Any) -> Any:
    """
    浅克隆
    
    Args:
        obj: 对象
        
    Returns:
        克隆结果
    """
    if isinstance(obj, list):
        return list(obj)
    if isinstance(obj, dict):
        return dict(obj)
    if isinstance(obj, tuple):
        return tuple(obj)
    return obj


def deep_clone(obj: Any) -> Any:
    """
    深克隆
    
    Args:
        obj: 对象
        
    Returns:
        深克隆结果
    """
    return copy.deepcopy(obj)


def clone_with(obj: Any, overrides: Dict) -> Any:
    """
    带覆盖的克隆
    
    Args:
        obj: 对象
        overrides: 覆盖属性
        
    Returns:
        克隆后的对象
    """
    if isinstance(obj, dict):
        result = dict(obj)
        result.update(overrides)
        return result
    if isinstance(obj, list):
        result = list(obj)
        return result
    return obj


def merge_clone(base: Any, *updates: Dict) -> Any:
    """
    合并克隆
    
    Args:
        base: 基础对象
        *updates: 更新对象
        
    Returns:
        合并后的对象
    """
    if isinstance(base, dict):
        result = dict(base)
        for update in updates:
            if isinstance(update, dict):
                result.update(update)
        return result
    if isinstance(base, list):
        result = list(base)
        for update in updates:
            if isinstance(update, list):
                result.extend(update)
        return result
    return base


class CloneBuilder:
    """
    克隆构建器
    """
    
    def __init__(self, obj: Any):
        """
        Args:
            obj: 源对象
        """
        self._obj = obj
    
    def shallow(self) -> Any:
        """浅克隆"""
        return shallow_clone(self._obj)
    
    def deep(self) -> Any:
        """深克隆"""
        return deep_clone(self._obj)
    
    def with_overrides(self, overrides: Dict) -> Any:
        """带覆盖"""
        return clone_with(self._obj, overrides)
    
    def merge(self, *updates: Dict) -> Any:
        """合并"""
        return merge_clone(self._obj, *updates)


# 导出
__all__ = [
    "shallow_clone",
    "deep_clone",
    "clone_with",
    "merge_clone",
    "CloneBuilder",
]
