"""
AsyncPool - 异步池
基于 Claude Code asyncPool.ts 设计

异步资源池。
"""
import asyncio
from typing import Any, Callable, Generic, List, Optional, TypeVar

T = TypeVar('T')


class AsyncPool(Generic[T]):
    """
    异步资源池
    
    复用有限数量的资源。
    """
    
    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 10,
        min_size: int = 1,
    ):
        """
        Args:
            factory: 资源工厂函数
            max_size: 最大池大小
            min_size: 最小池大小
        """
        self._factory = factory
        self._max_size = max_size
        self._min_size = min_size
        self._pool: List[T] = []
        self._in_use: set = set()
        self._lock = asyncio.Lock()
        self._size = 0
    
    async def acquire(self) -> T:
        """获取资源"""
        async with self._lock:
            # 先从池中取空闲资源
            while self._pool:
                resource = self._pool.pop()
                if self._validate_resource(resource):
                    self._in_use.add(resource)
                    return resource
                
                # 无效资源，销毁
                await self._destroy_resource(resource)
                self._size -= 1
            
            # 池中没有，创建新资源
            if self._size < self._max_size:
                resource = await self._create_resource()
                self._size += 1
                self._in_use.add(resource)
                return resource
            
            # 池已满，等待
            while True:
                self._lock.release()
                await asyncio.sleep(0.1)
                self._lock.acquire()
                
                # 再次尝试
                while self._pool:
                    resource = self._pool.pop()
                    if self._validate_resource(resource):
                        self._in_use.add(resource)
                        return resource
                    await self._destroy_resource(resource)
                    self._size -= 1
                
                if self._size < self._max_size:
                    resource = await self._create_resource()
                    self._size += 1
                    self._in_use.add(resource)
                    return resource
    
    async def release(self, resource: T) -> None:
        """释放资源"""
        async with self._lock:
            if resource in self._in_use:
                self._in_use.remove(resource)
                
                if self._validate_resource(resource):
                    self._pool.append(resource)
                else:
                    await self._destroy_resource(resource)
                    self._size -= 1
    
    async def _create_resource(self) -> T:
        """创建资源"""
        return self._factory()
    
    async def _destroy_resource(self, resource: T) -> None:
        """销毁资源"""
        if hasattr(resource, 'close'):
            resource.close()
    
    def _validate_resource(self, resource: T) -> bool:
        """验证资源是否有效"""
        if hasattr(resource, 'is_closed'):
            return not resource.is_closed
        return True
    
    async def clear(self) -> None:
        """清空池"""
        async with self._lock:
            for resource in self._pool:
                await self._destroy_resource(resource)
            self._pool.clear()
            self._size = 0
    
    @property
    def size(self) -> int:
        """当前池大小"""
        return self._size
    
    @property
    def available(self) -> int:
        """可用资源数"""
        return len(self._pool)


class PoolStats:
    """连接池统计"""
    
    def __init__(self):
        self.total = 0
        self.active = 0
        self.idle = 0
        self.waiting = 0


# 导出
__all__ = [
    "AsyncPool",
    "PoolStats",
]
