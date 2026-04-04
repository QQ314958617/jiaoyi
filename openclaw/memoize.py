"""
Memoize Utilities - 缓存工具
基于 Claude Code memoize.ts 设计

提供带TTL和LRU的缓存函数。
"""
import json
import threading
import time
from collections import OrderedDict
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')


class LRUCache:
    """
    LRU（最近最少使用）缓存
    
    当缓存满时，移除最久未使用的条目。
    """
    
    def __init__(self, max_size: int = 100):
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                return None
            # 移动到末尾（最近使用）
            self._cache.move_to_end(key)
            return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    # 移除最旧的
                    self._cache.popitem(last=False)
            self._cache[key] = value
    
    def has(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            return key in self._cache
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def peek(self, key: str) -> Optional[Any]:
        """查看缓存值（不更新顺序）"""
        with self._lock:
            return self._cache.get(key)


class TTLCache:
    """
    TTL（生存时间）缓存
    
    缓存值在指定时间后过期。
    """
    
    def __init__(self, ttl_ms: int = 5 * 60 * 1000):
        self._cache: dict[str, dict] = {}
        self._ttl_ms = ttl_ms
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值（检查TTL）"""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            age_ms = time.time() * 1000 - entry['timestamp']
            
            if age_ms > self._ttl_ms:
                # 过期，删除
                del self._cache[key]
                return None
            
            return entry['value']
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            self._cache[key] = {
                'value': value,
                'timestamp': time.time() * 1000,
            }
    
    def has(self, key: str) -> bool:
        """检查键是否存在且未过期"""
        return self.get(key) is not None
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()


def memoize_with_ttl(
    ttl_ms: int = 5 * 60 * 1000,
    cache: Optional[TTLCache] = None,
):
    """
    带TTL的缓存装饰器
    
    Args:
        ttl_ms: 生存时间（毫秒）
        cache: 可选的缓存实例
        
    Returns:
        装饰器函数
    """
    _cache = cache or TTLCache(ttl_ms)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 构建缓存键
            key = json.dumps({'args': args, 'kwargs': kwargs}, default=str)
            
            # 尝试从缓存获取
            cached = _cache.get(key)
            if cached is not None:
                return cached
            
            # 计算并缓存
            result = func(*args, **kwargs)
            _cache.set(key, result)
            return result
        
        # 添加缓存属性
        wrapper.cache = _cache
        return wrapper
    
    return decorator


def memoize_with_lru(max_size: int = 100):
    """
    带LRU的缓存装饰器
    
    Args:
        max_size: 最大缓存条目数
        
    Returns:
        装饰器函数
    """
    _cache = LRUCache(max_size)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 构建缓存键
            key = json.dumps({'args': args, 'kwargs': kwargs}, default=str)
            
            # 尝试从缓存获取
            cached = _cache.get(key)
            if cached is not None:
                return cached
            
            # 计算并缓存
            result = func(*args, **kwargs)
            _cache.set(key, result)
            return result
        
        # 添加缓存属性
        wrapper.cache = _cache
        return wrapper
    
    return decorator


def memoize(func: Callable[..., T]) -> Callable[..., T]:
    """
    简单缓存装饰器（无限TTL）
    
    Args:
        func: 要缓存的函数
        
    Returns:
        缓存版本的函数
    """
    _cache: dict[str, T] = {}
    _lock = threading.Lock()
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        key = json.dumps({'args': args, 'kwargs': kwargs}, default=str)
        
        with _lock:
            if key in _cache:
                return _cache[key]
        
        result = func(*args, **kwargs)
        
        with _lock:
            _cache[key] = result
        
        return result
    
    wrapper.cache = _cache
    return wrapper


# 导出
__all__ = [
    "LRUCache",
    "TTLCache",
    "memoize_with_ttl",
    "memoize_with_lru",
    "memoize",
]
