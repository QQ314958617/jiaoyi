"""
Cache - 缓存
基于 Claude Code cache.ts 设计

通用缓存实现。
"""
import time
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar('T')


class CacheEntry:
    """缓存条目"""
    
    def __init__(self, value: Any, ttl: Optional[float] = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_access = self.created_at
    
    def is_expired(self) -> bool:
        """是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class Cache(Generic[T]):
    """
    通用缓存
    
    支持TTL和LRU驱逐策略。
    """
    
    def __init__(self, max_size: int = 100, default_ttl: float = None):
        """
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒）
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: dict = {}
        self._access_order: list = []
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存值"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        if entry.is_expired():
            self.delete(key)
            return None
        
        # 更新访问顺序
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        entry.access_count += 1
        entry.last_access = time.time()
        
        return entry.value
    
    def set(self, key: str, value: T, ttl: float = None) -> None:
        """设置缓存值"""
        if key in self._cache:
            if key in self._access_order:
                self._access_order.remove(key)
        elif len(self._cache) >= self._max_size:
            # 驱逐最久未使用的
            oldest = self._access_order.pop(0)
            if oldest in self._cache:
                del self._cache[oldest]
        
        self._cache[key] = CacheEntry(value, ttl or self._default_ttl)
        self._access_order.append(key)
    
    def has(self, key: str) -> bool:
        """检查键是否存在"""
        if key not in self._cache:
            return False
        
        if self._cache[key].is_expired():
            self.delete(key)
            return False
        
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
        return True
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
    
    def size(self) -> int:
        """缓存大小"""
        return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired = [
            k for k, v in self._cache.items()
            if v.is_expired()
        ]
        
        for k in expired:
            self.delete(k)
        
        return len(expired)
    
    def keys(self):
        """获取所有键"""
        return list(self._cache.keys())
    
    def values(self):
        """获取所有值"""
        return [self._cache[k].value for k in self._cache if not self._cache[k].is_expired()]


def cached(ttl: float = None, max_size: int = 100):
    """
    缓存装饰器
    
    Args:
        ttl: TTL秒数
        max_size: 最大缓存大小
        
    Returns:
        装饰器
    """
    cache = Cache(max_size=max_size, default_ttl=ttl)
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # 构建缓存键
            key = f"{func.__name__}:{args}:{kwargs}"
            
            # 尝试从缓存获取
            result = cache.get(key)
            if result is not None:
                return result
            
            # 执行函数并缓存
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator


# 导出
__all__ = [
    "CacheEntry",
    "Cache",
    "cached",
]
