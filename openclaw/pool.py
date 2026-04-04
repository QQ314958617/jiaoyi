"""
Pool - 对象池
基于 Claude Code pool.ts 设计

对象池工具。
"""
import threading
from typing import Any, Callable, Optional


class Pool:
    """
    对象池
    
    复用对象，减少分配开销。
    """
    
    def __init__(self, factory: Callable, size: int = 10, max_size: int = 100):
        """
        Args:
            factory: 对象工厂
            size: 初始大小
            max_size: 最大大小
        """
        self._factory = factory
        self._max_size = max_size
        self._pool = []
        self._lock = threading.Lock()
        
        # 预创建
        for _ in range(size):
            self._pool.append(factory())
    
    def acquire(self) -> Any:
        """
        获取对象
        
        Returns:
            对象
        """
        with self._lock:
            if self._pool:
                return self._pool.pop()
            return self._factory()
    
    def release(self, obj: Any) -> None:
        """
        释放对象回池
        
        Args:
            obj: 对象
        """
        with self._lock:
            if len(self._pool) < self._max_size:
                self._pool.append(obj)
    
    def clear(self) -> None:
        """清空池"""
        with self._lock:
            self._pool.clear()
    
    @property
    def size(self) -> int:
        """当前池大小"""
        return len(self._pool)
    
    def __enter__(self) -> Any:
        return self.acquire()
    
    def __exit__(self, *args) -> None:
        pass


class PoolContext:
    """
    对象池上下文
    
    使用with语句自动获取/释放。
    """
    
    def __init__(self, pool: Pool):
        """
        Args:
            pool: 对象池
        """
        self._pool = pool
        self._obj = None
    
    def __enter__(self) -> Any:
        self._obj = self._pool.acquire()
        return self._obj
    
    def __exit__(self, *args) -> None:
        if self._obj is not None:
            self._pool.release(self._obj)


def create_pool(factory: Callable, size: int = 10, max_size: int = 100) -> Pool:
    """
    创建对象池
    
    Args:
        factory: 工厂函数
        size: 初始大小
        max_size: 最大大小
        
    Returns:
        Pool实例
    """
    return Pool(factory, size, max_size)


# 导出
__all__ = [
    "Pool",
    "PoolContext",
    "create_pool",
]
