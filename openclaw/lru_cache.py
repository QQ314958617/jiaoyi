"""
LRUCache - 最近最少使用缓存
基于 Claude Code lruCache.ts 设计

LRU缓存实现。
"""
from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    """
    最近最少使用缓存
    
    固定容量，超出时淘汰最久未使用的项。
    """
    
    def __init__(self, max_size: int = 100):
        """
        Args:
            max_size: 最大缓存数量
        """
        self._max_size = max_size
        self._cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 键
            
        Returns:
            缓存值或None
        """
        if key not in self._cache:
            return None
        
        # 移到末尾（最近使用）
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """
        设置缓存
        
        Args:
            key: 键
            value: 值
        """
        if key in self._cache:
            # 更新并移到末尾
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            # 检查容量
            if len(self._cache) >= self._max_size:
                # 移除最久未使用的（第一个）
                self._cache.popitem(last=False)
            
            self._cache[key] = value
    
    def has(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._cache
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    def size(self) -> int:
        """缓存大小"""
        return len(self._cache)
    
    def keys(self):
        """获取所有键"""
        return list(self._cache.keys())
    
    def values(self):
        """获取所有值"""
        return list(self._cache.values())
    
    def items(self):
        """获取所有项"""
        return list(self._cache.items())
    
    def peek(self, key: str) -> Optional[Any]:
        """
        查看缓存（不更新访问顺序）
        
        Args:
            key: 键
            
        Returns:
            缓存值或None
        """
        return self._cache.get(key)
    
    def remove_oldest(self) -> Optional[tuple]:
        """
        移除最久未使用的项
        
        Returns:
            (key, value) 或 None
        """
        if not self._cache:
            return None
        
        key = next(iter(self._cache))
        value = self._cache[key]
        del self._cache[key]
        return (key, value)


class TTLMap:
    """
    TTL映射
    
    带过期时间的键值对。
    """
    
    def __init__(self):
        self._data: dict = {}
        self._expiry: dict = {}
    
    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """设置（带TTL）"""
        import time
        self._data[key] = value
        self._expiry[key] = time.time() + ttl_seconds
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取"""
        import time
        
        if key not in self._data:
            return default
        
        if time.time() > self._expiry[key]:
            del self._data[key]
            del self._expiry[key]
            return default
        
        return self._data[key]
    
    def has(self, key: str) -> bool:
        """检查键是否存在且未过期"""
        import time
        
        if key not in self._data:
            return False
        
        if time.time() > self._expiry[key]:
            del self._data[key]
            del self._expiry[key]
            return False
        
        return True
    
    def delete(self, key: str) -> bool:
        """删除"""
        if key in self._data:
            del self._data[key]
            del self._expiry[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空"""
        self._data.clear()
        self._expiry.clear()
    
    def cleanup(self) -> int:
        """清理过期项"""
        import time
        now = time.time()
        expired = [k for k, t in self._expiry.items() if now > t]
        
        for k in expired:
            del self._data[k]
            del self._expiry[k]
        
        return len(expired)


# 导出
__all__ = [
    "LRUCache",
    "TTLMap",
]
