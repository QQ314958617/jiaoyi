"""
Map2 - 映射
基于 Claude Code map.ts 设计

映射/字典工具。
"""
from typing import Any, Callable, Dict, Iterable, List, Optional


class Map:
    """
    映射（包装Python内置dict）
    """
    
    def __init__(self, items: Dict = None):
        """
        Args:
            items: 初始字典
        """
        self._map = dict(items) if items else {}
    
    def get(self, key: Any, default: Any = None) -> Any:
        """获取"""
        return self._map.get(key, default)
    
    def set(self, key: Any, value: Any) -> None:
        """设置"""
        self._map[key] = value
    
    def has(self, key: Any) -> bool:
        """检查"""
        return key in self._map
    
    def delete(self, key: Any) -> bool:
        """删除"""
        if key in self._map:
            del self._map[key]
            return True
        return False
    
    def keys(self) -> List:
        """所有键"""
        return list(self._map.keys())
    
    def values(self) -> List:
        """所有值"""
        return list(self._map.values())
    
    def items(self) -> List:
        """所有项"""
        return list(self._map.items())
    
    def is_empty(self) -> bool:
        return len(self._map) == 0
    
    def size(self) -> int:
        return len(self._map)
    
    def clear(self) -> None:
        self._map.clear()
    
    def update(self, other: Dict) -> None:
        """更新"""
        self._map.update(other)
    
    def __len__(self) -> int:
        return len(self._map)
    
    def __getitem__(self, key):
        return self._map[key]
    
    def __setitem__(self, key, value):
        self._map[key] = value
    
    def __contains__(self, key):
        return key in self._map
    
    def __iter__(self):
        return iter(self._map)


def map_values(items: Dict, fn: Callable) -> Dict:
    """
    映射值
    
    Args:
        items: 字典
        fn: 值变换函数
        
    Returns:
        新字典
    """
    return {k: fn(v) for k, v in items.items()}


def map_keys(items: Dict, fn: Callable) -> Dict:
    """
    映射键
    
    Args:
        items: 字典
        fn: 键变换函数
        
    Returns:
        新字典
    """
    return {fn(k): v for k, v in items.items()}


def invert(items: Dict) -> Dict:
    """
    反转映射
    
    Args:
        items: 字典
        
    Returns:
        键值互换的字典
    """
    return {v: k for k, v in items.items()}


def pick(source: Dict, *keys) -> Dict:
    """
    挑选键
    
    Args:
        source: 源字典
        *keys: 要保留的键
        
    Returns:
        新字典
    """
    return {k: source[k] for k in keys if k in source}


def omit(source: Dict, *keys) -> Dict:
    """
    排除键
    
    Args:
        source: 源字典
        *keys: 要排除的键
        
    Returns:
        新字典
    """
    return {k: v for k, v in source.items() if k not in keys}


def merge(*dicts: Dict) -> Dict:
    """
    合并字典
    
    Args:
        *dicts: 字典列表
        
    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def group_by(items: List, key_fn: Callable) -> Dict:
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


# 导出
__all__ = [
    "Map",
    "map_values",
    "map_keys",
    "invert",
    "pick",
    "omit",
    "merge",
    "group_by",
]
