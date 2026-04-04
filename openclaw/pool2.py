"""
Pool2 - 对象池2
基于 Claude Code pool2.ts 设计

对象池实现。
"""
import threading
from typing import Any, Callable, Generic, List, Optional, TypeVar

T = TypeVar('T')


class ObjectPool(Generic[T]):
    """
    对象池
    
    复用对象实例。
    """
    
    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 10,
        reset: Callable[[T], None] = None,
    ):
        """
        Args:
            factory: 对象工厂
            max_size: 最大池大小
            reset: 重置函数
        """
        self._factory = factory
        self._max_size = max_size
        self._reset = reset
        
        self._pool: List[T] = []
        self._lock = threading.Lock()
        self._size = 0
    
    def acquire(self) -> T:
        """获取对象"""
        with self._lock:
            if self._pool:
                return self._pool.pop()
            
            if self._size < self._max_size:
                self._size += 1
                return self._factory()
            
            # 等待或创建新对象
            return self._factory()
    
    def release(self, obj: T) -> None:
        """释放对象"""
        with self._lock:
            if len(self._pool) < self._max_size:
                if self._reset:
                    self._reset(obj)
                self._pool.append(obj)
    
    def clear(self) -> None:
        """清空池"""
        with self._lock:
            self._pool.clear()
    
    @property
    def size(self) -> int:
        """当前池大小"""
        with self._lock:
            return len(self._pool)


class PoolItem:
    """
    池项目包装器
    
    使用上下文管理器自动归还。
    """
    
    def __init__(self, pool: ObjectPool, item: T):
        self._pool = pool
        self._item = item
    
    @property
    def item(self) -> T:
        return self._item
    
    def __enter__(self) -> T:
        return self._item
    
    def __exit__(self, *args) -> None:
        self._pool.release(self._item)


# 导出
__all__ = [
    "ObjectPool",
    "PoolItem",
]
