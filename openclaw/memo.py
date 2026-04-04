"""
Memo - 记忆化
基于 Claude Code memo.ts 设计

记忆化工具。
"""
from typing import Any, Callable, Dict, Optional
import hashlib
import pickle


def memoize(fn: Callable = None, *, max_size: int = 128) -> Callable:
    """
    记忆化装饰器
    
    Args:
        fn: 要记忆化的函数
        max_size: 缓存大小
        
    Returns:
        装饰后的函数
    """
    cache: Dict[str, Any] = {}
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # 构建缓存键
            key = _make_key(args, kwargs)
            
            if key in cache:
                return cache[key]
            
            result = func(*args, **kwargs)
            
            # 限制缓存大小
            if len(cache) >= max_size:
                # 简单策略：清空一半
                keys = list(cache.keys())[:max_size // 2]
                for k in keys:
                    del cache[k]
            
            cache[key] = result
            return result
        
        wrapper.cache = cache
        wrapper.cache_clear = lambda: cache.clear()
        return wrapper
    
    if fn is not None:
        return decorator(fn)
    return decorator


def memoize_async(fn: Callable = None, *, max_size: int = 128) -> Callable:
    """
    异步记忆化装饰器
    
    Args:
        fn: 要记忆化的异步函数
        max_size: 缓存大小
        
    Returns:
        装饰后的异步函数
    """
    cache: Dict[str, Any] = {}
    
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            
            if key in cache:
                return cache[key]
            
            result = await func(*args, **kwargs)
            
            if len(cache) >= max_size:
                keys = list(cache.keys())[:max_size // 2]
                for k in keys:
                    del cache[k]
            
            cache[key] = result
            return result
        
        wrapper.cache = cache
        wrapper.cache_clear = lambda: cache.clear()
        return wrapper
    
    if fn is not None:
        return decorator(fn)
    return decorator


def _make_key(args: tuple, kwargs: dict) -> str:
    """生成缓存键"""
    try:
        key = pickle.dumps((args, sorted(kwargs.items())))
        return hashlib.md5(key).hexdigest()
    except Exception:
        # 回退到字符串表示
        return str((args, sorted(kwargs.items())))


class MemoCache:
    """
    记忆化缓存
    
    手动管理的缓存。
    """
    
    def __init__(self, max_size: int = 128):
        self._cache: Dict[str, Any] = {}
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存"""
        if len(self._cache) >= self._max_size:
            # 清空一半
            keys = list(self._cache.keys())[:self._max_size // 2]
            for k in keys:
                del self._cache[k]
        
        self._cache[key] = value
    
    def has(self, key: str) -> bool:
        """是否存在"""
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


def memoize_with_cache(cache: MemoCache):
    """
    使用指定缓存的记忆化
    
    Args:
        cache: MemoCache实例
    """
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            
            if cache.has(key):
                return cache.get(key)
            
            result = fn(*args, **kwargs)
            cache.set(key, result)
            return result
        
        return wrapper
    
    return decorator


# 导出
__all__ = [
    "memoize",
    "memoize_async",
    "MemoCache",
    "memoize_with_cache",
]
