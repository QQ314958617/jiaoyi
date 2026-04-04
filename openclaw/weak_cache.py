"""
Weak Cache - 弱引用缓存
基于 Claude Code weakCache.ts 设计

使用弱引用的缓存，避免内存泄漏。
"""
import weakref
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar('T')


class WeakCache(Generic[T]):
    """
    弱引用缓存
    
    当对象没有被其他强引用时自动被GC回收。
    """
    
    def __init__(self, max_size: int = 128):
        self._cache: dict = {}
        self._max_size = max_size
        self._access_order: list = []
    
    def get(self, key: str) -> Optional[T]:
        """获取缓存值"""
        if key not in self._cache:
            return None
        
        ref = self._cache[key]
        value = ref()
        
        if value is None:
            del self._cache[key]
            return None
        
        # 更新访问顺序
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        return value
    
    def set(self, key: str, value: T) -> None:
        """设置缓存值"""
        if key in self._cache:
            if key in self._access_order:
                self._access_order.remove(key)
        elif len(self._cache) >= self._max_size:
            # 移除最久未访问的
            oldest = self._access_order.pop(0)
            if oldest in self._cache:
                del self._cache[oldest]
        
        self._cache[key] = weakref.ref(value)
        self._access_order.append(key)
    
    def has(self, key: str) -> bool:
        """检查键是否存在"""
        return self.get(key) is not None
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._access_order.clear()
    
    def size(self) -> int:
        """缓存大小"""
        return len(self._cache)


class WeakMapCache:
    """
    基于WeakMap的缓存
    
    键为对象，值强引用。
    """
    
    def __init__(self):
        self._map = weakref.WeakMap()
    
    def set(self, key: object, value: T) -> None:
        """设置缓存"""
        self._map[key] = value
    
    def get(self, key: object) -> Optional[T]:
        """获取缓存"""
        try:
            return self._map[key]
        except KeyError:
            return None
        except TypeError:
            # 对象不可哈希
            return None
    
    def has(self, key: object) -> bool:
        """检查是否存在"""
        try:
            return key in self._map
        except TypeError:
            return False
    
    def delete(self, key: object) -> bool:
        """删除"""
        try:
            if key in self._map:
                del self._map[key]
                return True
            return False
        except (KeyError, TypeError):
            return False


# 导出
__all__ = [
    "WeakCache",
    "WeakMapCache",
]
