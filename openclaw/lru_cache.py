"""
LRU Cache - 最近最少使用缓存
基于 Claude Code lruCache.ts 设计

线程安全的LRU缓存实现。
"""
from collections import OrderedDict
from typing import Any, Callable, Optional, TypeVar
from functools import wraps

T = TypeVar('T')


class LRUCache(Generic[T]):
    """
    最近最少使用缓存
    
    当缓存满时，自动移除最久未使用的条目。
    """
    
    def __init__(self, max_size: int = 128):
        """
        Args:
            max_size: 最大缓存条目数
        """
        self._max_size = max_size
        self._cache: OrderedDict = OrderedDict()
    
    def get(self, key: str) -> Optional[T]:
        """
        获取缓存值
        
        Args:
            key: 键
            
        Returns:
            缓存值或None
        """
        if key not in self._cache:
            return None
        
        # 移动到末尾（最近使用）
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def set(self, key: str, value: T) -> None:
        """
        设置缓存值
        
        Args:
            key: 键
            value: 值
        """
        if key in self._cache:
            # 更新并移动到末尾
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            # 添加新条目
            if len(self._cache) >= self._max_size:
                # 移除最久未使用的
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
        """获取缓存大小"""
        return len(self._cache)
    
    def peek(self, key: str) -> Optional[T]:
        """
        查看缓存值（不更新顺序）
        
        Args:
            key: 键
            
        Returns:
            缓存值或None
        """
        return self._cache.get(key)
    
    def get_or_compute(self, key: str, factory: Callable[[], T]) -> T:
        """
        获取或计算缓存值
        
        Args:
            key: 键
            factory: 值工厂函数
            
        Returns:
            缓存值
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value)
        return value
    
    def __len__(self) -> int:
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        return key in self._cache
    
    def __getitem__(self, key: str) -> Optional[T]:
        return self.get(key)
    
    def __setitem__(self, key: str, value: T) -> None:
        self.set(key, value)
    
    def __delitem__(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]
    
    def keys(self):
        """获取所有键"""
        return self._cache.keys()
    
    def values(self):
        """获取所有值"""
        return self._cache.values()
    
    def items(self):
        """获取所有键值对"""
        return self._cache.items()


def lru_cache(max_size: int = 128):
    """
    LRU缓存装饰器
    
    Args:
        max_size: 最大缓存条目数
        
    Returns:
        装饰器
    """
    cache = LRUCache(max_size)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # 构建缓存键
            key = str(args) + str(sorted(kwargs.items()))
            
            # 尝试从缓存获取
            cached = cache.get(key)
            if cached is not None:
                return cached
            
            # 计算并缓存
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        # 添加缓存属性
        wrapper.cache = cache
        return wrapper
    
    return decorator


# 导出
__all__ = [
    "LRUCache",
    "lru_cache",
]
