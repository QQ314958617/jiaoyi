"""
Index - 索引
基于 Claude Code index.ts 设计

索引工具。
"""
from typing import Any, Callable, Dict, List, Optional


class Index:
    """
    索引
    
    按字段建立快速查找索引。
    """
    
    def __init__(self, items: List[dict] = None, key: str = None):
        """
        Args:
            items: 初始项列表
            key: 键名
        """
        self._index: Dict[Any, Any] = {}
        
        if items and key:
            for item in items:
                if isinstance(item, dict):
                    self.put(item.get(key), item)
    
    def put(self, key: Any, value: Any) -> None:
        """
        添加到索引
        
        Args:
            key: 键
            value: 值
        """
        self._index[key] = value
    
    def get(self, key: Any) -> Optional[Any]:
        """
        获取
        
        Args:
            key: 键
            
        Returns:
            值或None
        """
        return self._index.get(key)
    
    def has(self, key: Any) -> bool:
        """检查键是否存在"""
        return key in self._index
    
    def remove(self, key: Any) -> bool:
        """移除"""
        if key in self._index:
            del self._index[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空"""
        self._index.clear()
    
    def keys(self) -> List:
        """所有键"""
        return list(self._index.keys())
    
    def values(self) -> List:
        """所有值"""
        return list(self._index.values())
    
    def items(self) -> List:
        """所有项"""
        return list(self._index.items())
    
    @property
    def size(self) -> int:
        return len(self._index)


class MultiIndex:
    """
    多值索引
    
    一个键对应多个值。
    """
    
    def __init__(self):
        self._index: Dict[Any, set] = {}
    
    def put(self, key: Any, value: Any) -> None:
        """添加"""
        if key not in self._index:
            self._index[key] = set()
        self._index[key].add(value)
    
    def get(self, key: Any) -> set:
        """获取所有值"""
        return self._index.get(key, set()).copy()
    
    def has(self, key: Any, value: Any = None) -> bool:
        """检查"""
        if key not in self._index:
            return False
        if value is None:
            return True
        return value in self._index[key]
    
    def remove(self, key: Any, value: Any = None) -> None:
        """移除"""
        if key not in self._index:
            return
        
        if value is None:
            del self._index[key]
        else:
            self._index[key].discard(value)
            if not self._index[key]:
                del self._index[key]
    
    def clear(self) -> None:
        """清空"""
        self._index.clear()


def create_index(items: List[dict], key: str) -> Index:
    """
    创建索引
    
    Args:
        items: 项列表
        key: 键名
        
    Returns:
        Index实例
    """
    return Index(items, key)


# 导出
__all__ = [
    "Index",
    "MultiIndex",
    "create_index",
]
