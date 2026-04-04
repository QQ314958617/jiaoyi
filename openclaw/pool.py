"""
Pool - 对象池
基于 Claude Code pool.ts 设计

可复用对象的池化管理。
"""
import threading
import queue
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar('T')


class ObjectPool(Generic[T]):
    """
    对象池
    
    管理可复用对象的生命周期，减少GC压力。
    """
    
    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 10,
        reset: Optional[Callable[[T], None]] = None,
    ):
        """
        Args:
            factory: 对象工厂函数
            max_size: 最大池大小
            reset: 可选的重置函数，在归还对象时调用
        """
        self._factory = factory
        self._max_size = max_size
        self._reset = reset
        self._pool: queue.Queue = queue.Queue()
        self._created = 0
        self._lock = threading.Lock()
    
    def acquire(self) -> T:
        """
        获取对象
        
        Returns:
            对象
        """
        try:
            obj = self._pool.get_nowait()
            return obj
        except queue.Empty:
            with self._lock:
                self._created += 1
            return self._factory()
    
    def release(self, obj: T) -> None:
        """
        归还对象
        
        Args:
            obj: 对象
        """
        # 重置对象
        if self._reset:
            try:
                self._reset(obj)
            except Exception:
                pass
        
        # 尝试放回池中
        try:
            self._pool.put_nowait(obj)
        except queue.Full:
            # 池已满，丢弃对象
            pass
    
    def clear(self) -> int:
        """
        清空池
        
        Returns:
            清空的对象数量
        """
        count = 0
        while True:
            try:
                self._pool.get_nowait()
                count += 1
            except queue.Empty:
                break
        
        with self._lock:
            self._created = 0
        
        return count
    
    @property
    def size(self) -> int:
        """当前池大小"""
        return self._pool.qsize()
    
    @property
    def created(self) -> int:
        """创建的对象总数"""
        with self._lock:
            return self._created


class PooledObject(Generic[T]):
    """
    池化对象包装器
    
    使用上下文管理器自动归还对象。
    """
    
    def __init__(self, pool: ObjectPool, obj: T):
        self._pool = pool
        self._obj = obj
        self._released = False
    
    @property
    def value(self) -> T:
        """获取对象"""
        return self._obj
    
    def release(self) -> None:
        """归还对象"""
        if not self._released:
            self._released = True
            self._pool.release(self._obj)
    
    def __enter__(self) -> T:
        return self._obj
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


def create_pool(
    factory: Callable[[], T],
    max_size: int = 10,
    reset: Optional[Callable[[T], None]] = None,
) -> ObjectPool[T]:
    """
    创建对象池
    
    Args:
        factory: 对象工厂
        max_size: 最大大小
        reset: 重置函数
        
    Returns:
        对象池
    """
    return ObjectPool(factory, max_size, reset)


# 导出
__all__ = [
    "ObjectPool",
    "PooledObject",
    "create_pool",
]
