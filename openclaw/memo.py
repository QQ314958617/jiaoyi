"""
Memo - 记忆化
基于 Claude Code memo.ts 设计

记忆化工具。
"""
from typing import Any, Callable, Dict


def memoize(fn: Callable) -> Callable:
    """
    记忆化装饰器
    
    Args:
        fn: 函数
        
    Returns:
        记忆化后的函数
    """
    cache: Dict = {}
    
    def wrapper(*args, **kwargs):
        # 创建可哈希的键
        key = str(args) + str(sorted(kwargs.items()))
        
        if key not in cache:
            cache[key] = fn(*args, **kwargs)
        
        return cache[key]
    
    wrapper.cache = cache
    wrapper.clear_cache = lambda: cache.clear()
    return wrapper


def memoize_with_key(key_fn: Callable) -> Callable:
    """
    带自定义键的记忆化
    
    Args:
        key_fn: 键生成函数
        
    Returns:
        装饰器
    """
    def decorator(fn: Callable) -> Callable:
        cache: Dict = {}
        
        def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            
            if key not in cache:
                cache[key] = fn(*args, **kwargs)
            
            return cache[key]
        
        wrapper.cache = cache
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    
    return decorator


class MemoCache:
    """
    记忆化缓存
    """
    
    def __init__(self, ttl: float = None):
        """
        Args:
            ttl: 过期时间（秒）
        """
        self._cache: Dict = {}
        self._ttl = ttl
    
    def get(self, key: str) -> Any:
        """获取"""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """设置"""
        self._cache[key] = value
    
    def has(self, key: str) -> bool:
        """检查"""
        return key in self._cache
    
    def delete(self, key: str) -> bool:
        """删除"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空"""
        self._cache.clear()
    
    @property
    def size(self) -> int:
        return len(self._cache)


# 导出
__all__ = [
    "memoize",
    "memoize_with_key",
    "MemoCache",
]
