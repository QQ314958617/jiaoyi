"""
Cache - 缓存
基于 Claude Code cache.ts 设计

缓存工具。
"""
import time
from typing import Any, Callable, Optional


class Cache:
    """简单缓存"""
    
    def __init__(self, ttl: float = None):
        """
        Args:
            ttl: 生存时间（秒）
        """
        self._cache = {}
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # 检查过期
        if self._ttl is not None:
            if time.time() - entry["time"] > self._ttl:
                del self._cache[key]
                return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存"""
        self._cache[key] = {
            "value": value,
            "time": time.time()
        }
    
    def has(self, key: str) -> bool:
        """是否存在"""
        return self.get(key) is not None
    
    def delete(self, key: str) -> None:
        """删除缓存"""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    def memoize(self, fn: Callable) -> Callable:
        """记忆化函数"""
        def memoized(*args, **kwargs):
            key = str(args) + str(kwargs)
            result = self.get(key)
            if result is None:
                result = fn(*args, **kwargs)
                self.set(key, result)
            return result
        return memoized


def memoize(fn: Callable) -> Callable:
    """
    简单记忆化装饰器
    """
    cache = {}
    
    def memoized(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = fn(*args, **kwargs)
        return cache[key]
    
    memoized.cache = cache
    return memoized


def memoize_ttl(ttl: float = 60) -> Callable:
    """带TTL的记忆化"""
    def decorator(fn: Callable) -> Callable:
        cache = {}
        
        def memoized(*args, **kwargs):
            key = str(args) + str(kwargs)
            now = time.time()
            
            if key in cache:
                value, timestamp = cache[key]
                if now - timestamp < ttl:
                    return value
            
            result = fn(*args, **kwargs)
            cache[key] = (result, now)
            return result
        
        memoized.cache = cache
        return memoized
    
    return decorator


# 导出
__all__ = [
    "Cache",
    "memoize",
    "memoize_ttl",
]
