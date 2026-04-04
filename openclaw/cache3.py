"""
Cache3 - 缓存
基于 Claude Code cache.ts 设计

缓存工具。
"""
import time
from typing import Any, Callable, Dict, Optional


class Cache:
    """
    缓存
    """
    
    def __init__(self, ttl: float = 60):
        """
        Args:
            ttl: 过期时间（秒）
        """
        self._ttl = ttl
        self._store: Dict[str, tuple] = {}  # key -> (value, expire_time)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        if key in self._store:
            value, expire_time = self._store[key]
            if time.time() < expire_time:
                return value
            del self._store[key]
        return default
    
    def set(self, key: str, value: Any, ttl: float = None) -> None:
        """
        设置
        
        Args:
            key: 键
            value: 值
            ttl: 过期时间（秒）
        """
        expire_time = time.time() + (ttl if ttl is not None else self._ttl)
        self._store[key] = (value, expire_time)
    
    def has(self, key: str) -> bool:
        """是否存在且未过期"""
        if key in self._store:
            _, expire_time = self._store[key]
            if time.time() < expire_time:
                return True
            del self._store[key]
        return False
    
    def delete(self, key: str) -> bool:
        """删除"""
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空"""
        self._store.clear()
    
    def cleanup(self) -> int:
        """清理过期项"""
        now = time.time()
        expired = [k for k, (_, t) in self._store.items() if now >= t]
        for k in expired:
            del self._store[k]
        return len(expired)
    
    @property
    def size(self) -> int:
        return len(self._store)


class TTLCache:
    """
    TTL缓存（别名）
    """
    
    def __init__(self, ttl: float = 60, max_size: int = 100):
        self._ttl = ttl
        self._max_size = max_size
        self._cache = Cache(ttl)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, default)
    
    def set(self, key: str, value: Any, ttl: float = None) -> None:
        return self._cache.set(key, value, ttl)
    
    def has(self, key: str) -> bool:
        return self._cache.has(key)
    
    def delete(self, key: str) -> bool:
        return self._cache.delete(key)
    
    def clear(self) -> None:
        self._cache.clear()


def memoize_ttl(ttl: float = 60) -> Callable:
    """
    TTL记忆化装饰器
    
    Args:
        ttl: 过期时间
        
    Returns:
        装饰器
    """
    cache = Cache(ttl)
    
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            
            if cache.has(key):
                return cache.get(key)
            
            result = fn(*args, **kwargs)
            cache.set(key, result)
            return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator


# 导出
__all__ = [
    "Cache",
    "TTLCache",
    "memoize_ttl",
]
