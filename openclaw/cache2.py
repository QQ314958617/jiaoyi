"""
Cache2 - 缓存
基于 Claude Code cache.ts 设计

缓存工具。
"""
import time
from typing import Any, Callable, Dict, Optional


class Cache:
    """
    简单缓存
    
    基于时间的缓存。
    """
    
    def __init__(self, ttl: float = 60):
        """
        Args:
            ttl: 过期时间（秒）
        """
        self._ttl = ttl
        self._cache: Dict[str, tuple] = {}  # key -> (value, expire_time)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        if key in self._cache:
            value, expire_time = self._cache[key]
            if time.time() < expire_time:
                return value
            del self._cache[key]
        
        return default
    
    def set(self, key: str, value: Any, ttl: float = None) -> None:
        """
        设置
        
        Args:
            key: 键
            value: 值
            ttl: 过期时间（秒）
        """
        expire_time = time.time() + (ttl or self._ttl)
        self._cache[key] = (value, expire_time)
    
    def has(self, key: str) -> bool:
        """检查是否存在且未过期"""
        if key in self._cache:
            _, expire_time = self._cache[key]
            if time.time() < expire_time:
                return True
            del self._cache[key]
        return False
    
    def delete(self, key: str) -> bool:
        """删除"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空"""
        self._cache.clear()
    
    def cleanup(self) -> int:
        """
        清理过期项
        
        Returns:
            清理数量
        """
        now = time.time()
        expired = [
            k for k, (_, expire_time) in self._cache.items()
            if now >= expire_time
        ]
        
        for k in expired:
            del self._cache[k]
        
        return len(expired)


class LRUCache:
    """
    LRU缓存
    
    最近最少使用淘汰。
    """
    
    def __init__(self, capacity: int = 100):
        """
        Args:
            capacity: 容量
        """
        self._capacity = capacity
        self._cache: Dict[str, Any] = {}
        self._order: list = []
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取"""
        if key in self._cache:
            self._order.remove(key)
            self._order.append(key)
            return self._cache[key]
        return default
    
    def set(self, key: str, value: Any) -> None:
        """设置"""
        if key in self._cache:
            self._order.remove(key)
        elif len(self._cache) >= self._capacity:
            oldest = self._order.pop(0)
            del self._cache[oldest]
        
        self._cache[key] = value
        self._order.append(key)
    
    def has(self, key: str) -> bool:
        return key in self._cache
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            self._order.remove(key)
            return True
        return False
    
    def clear(self) -> None:
        self._cache.clear()
        self._order.clear()
    
    @property
    def size(self) -> int:
        return len(self._cache)


# 导出
__all__ = [
    "Cache",
    "LRUCache",
]
