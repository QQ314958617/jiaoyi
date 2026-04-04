"""
BiMap - 双向映射
基于 Claude Code bimap.ts 设计

双向映射工具。
"""
from typing import Any, Dict, Optional


class BiMap:
    """
    双向映射
    
    支持正向和反向查找。
    """
    
    def __init__(self):
        self._forward: Dict[Any, Any] = {}
        self._reverse: Dict[Any, Any] = {}
    
    def put(self, key: Any, value: Any) -> None:
        """
        添加映射
        
        Args:
            key: 键
            value: 值
        """
        # 移除旧映射
        if key in self._forward:
            old_value = self._forward[key]
            del self._reverse[old_value]
        
        if value in self._reverse:
            old_key = self._reverse[value]
            del self._forward[old_key]
        
        self._forward[key] = value
        self._reverse[value] = key
    
    def get(self, key: Any) -> Optional[Any]:
        """
        正向查找
        
        Args:
            key: 键
            
        Returns:
            值或None
        """
        return self._forward.get(key)
    
    def get_key(self, value: Any) -> Optional[Any]:
        """
        反向查找
        
        Args:
            value: 值
            
        Returns:
            键或None
        """
        return self._reverse.get(value)
    
    def has_key(self, key: Any) -> bool:
        """检查键是否存在"""
        return key in self._forward
    
    def has_value(self, value: Any) -> bool:
        """检查值是否存在"""
        return value in self._reverse
    
    def remove_key(self, key: Any) -> bool:
        """移除键"""
        if key in self._forward:
            value = self._forward[key]
            del self._forward[key]
            del self._reverse[value]
            return True
        return False
    
    def remove_value(self, value: Any) -> bool:
        """移除值"""
        if value in self._reverse:
            key = self._reverse[value]
            del self._reverse[value]
            del self._forward[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空"""
        self._forward.clear()
        self._reverse.clear()
    
    def size(self) -> int:
        """大小"""
        return len(self._forward)
    
    def keys(self):
        """获取所有键"""
        return list(self._forward.keys())
    
    def values(self):
        """获取所有值"""
        return list(self._forward.values())
    
    def items(self):
        """获取所有映射"""
        return list(self._forward.items())
    
    def __len__(self) -> int:
        return self.size()
    
    def __contains__(self, item) -> bool:
        return item in self._forward or item in self._reverse


class MultiBiMap:
    """
    多值双向映射
    
    一个键对应多个值。
    """
    
    def __init__(self):
        self._forward: Dict[Any, set] = {}
        self._reverse: Dict[Any, set] = {}
    
    def put(self, key: Any, value: Any) -> None:
        """添加映射"""
        if key not in self._forward:
            self._forward[key] = set()
        self._forward[key].add(value)
        
        if value not in self._reverse:
            self._reverse[value] = set()
        self._reverse[value].add(key)
    
    def get(self, key: Any) -> set:
        """获取键对应的所有值"""
        return self._forward.get(key, set()).copy()
    
    def get_key(self, value: Any) -> set:
        """获取值对应的所有键"""
        return self._reverse.get(value, set()).copy()
    
    def remove(self, key: Any, value: Any) -> bool:
        """移除映射"""
        if key in self._forward and value in self._forward[key]:
            self._forward[key].remove(value)
            if not self._forward[key]:
                del self._forward[key]
            
            if value in self._reverse:
                self._reverse[value].remove(key)
                if not self._reverse[value]:
                    del self._reverse[value]
            return True
        return False
    
    def clear(self) -> None:
        """清空"""
        self._forward.clear()
        self._reverse.clear()


# 导出
__all__ = [
    "BiMap",
    "MultiBiMap",
]
