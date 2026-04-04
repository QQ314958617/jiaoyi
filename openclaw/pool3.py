"""
Pool3 - 对象池3
基于 Claude Code pool3.ts 设计

更多对象池模式。
"""
import asyncio
from typing import Any, Callable, Generic, List, Optional, TypeVar

T = TypeVar('T')


class AsyncObjectPool(Generic[T]):
    """
    异步对象池
    """
    
    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 10,
        cleanup: Callable[[T], None] = None,
    ):
        """
        Args:
            factory: 工厂函数
            max_size: 最大大小
            cleanup: 清理函数
        """
        self._factory = factory
        self._max_size = max_size
        self._cleanup = cleanup or (lambda x: None)
        
        self._pool: List[T] = []
        self._size = 0
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> T:
        """获取对象"""
        async with self._lock:
            if self._pool:
                return self._pool.pop()
            
            if self._size < self._max_size:
                self._size += 1
                return self._factory()
            
            # 等待可用对象
            while not self._pool:
                await asyncio.sleep(0.1)
            
            return self._pool.pop()
    
    async def release(self, obj: T) -> None:
        """释放对象"""
        async with self._lock:
            self._pool.append(obj)
    
    async def clear(self) -> None:
        """清空池"""
        async with self._lock:
            for obj in self._pool:
                self._cleanup(obj)
            self._pool.clear()


class PoolConfig:
    """连接池配置"""
    
    def __init__(
        self,
        min_size: int = 1,
        max_size: int = 10,
        max_idle_time: float = 60.0,
        acquire_timeout: float = 30.0,
        idle_timeout: float = 300.0,
    ):
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time
        self.acquire_timeout = acquire_timeout
        self.idle_timeout = idle_timeout


class PoolStats:
    """池统计"""
    
    def __init__(self):
        self.total = 0
        self.active = 0
        self.idle = 0
        self.waiting = 0
        self.hits = 0
        self.misses = 0
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


# 导出
__all__ = [
    "AsyncObjectPool",
    "PoolConfig",
    "PoolStats",
]
