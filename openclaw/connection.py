"""
Connection - 连接管理
基于 Claude Code connection.ts 设计

连接池管理。
"""
import asyncio
import time
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar('T')


class Connection(Generic[T]):
    """
    连接包装器
    
    管理连接的生命周期。
    """
    
    def __init__(
        self,
        raw_connection: T,
        factory: Callable[[], T] = None,
        validate: Callable[[T], bool] = None,
        close: Callable[[T], None] = None,
    ):
        """
        Args:
            raw_connection: 原始连接
            factory: 工厂函数
            validate: 验证函数
            close: 关闭函数
        """
        self._conn = raw_connection
        self._factory = factory
        self._validate = validate or (lambda x: True)
        self._close = close or (lambda x: None)
        
        self._created_at = time.time()
        self._last_used = self._created_at
        self._use_count = 0
    
    @property
    def raw(self) -> T:
        """获取原始连接"""
        self._last_used = time.time()
        self._use_count += 1
        return self._conn
    
    def is_valid(self) -> bool:
        """连接是否有效"""
        return self._validate(self._conn)
    
    def age(self) -> float:
        """连接年龄（秒）"""
        return time.time() - self._created_at
    
    def idle_time(self) -> float:
        """空闲时间（秒）"""
        return time.time() - self._last_used
    
    def close(self) -> None:
        """关闭连接"""
        self._close(self._conn)
    
    @property
    def use_count(self) -> int:
        """使用次数"""
        return self._use_count


class ConnectionPool(Generic[T]):
    """
    连接池
    
    管理连接的创建、验证和回收。
    """
    
    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 10,
        min_size: int = 1,
        max_idle_ms: int = 60000,
        max_lifetime_ms: int = 300000,
        validate: Callable[[T], bool] = None,
        close: Callable[[T], None] = None,
    ):
        """
        Args:
            factory: 连接工厂
            max_size: 最大连接数
            min_size: 最小连接数
            max_idle_ms: 最大空闲时间
            max_lifetime_ms: 最大生命周期
            validate: 验证函数
            close: 关闭函数
        """
        self._factory = factory
        self._max_size = max_size
        self._min_size = min_size
        self._max_idle_ms = max_idle_ms
        self._max_lifetime_ms = max_lifetime_ms
        
        self._validate = validate or (lambda x: True)
        self._close = close or (lambda x: None)
        
        self._connections: list = []
        self._in_use: set = set()
        self._lock = asyncio.Lock()
        self._size = 0
    
    async def acquire(self) -> Connection[T]:
        """获取连接"""
        async with self._lock:
            # 查找可用连接
            while self._connections:
                conn_wrapper = self._connections.pop()
                
                # 检查连接是否有效
                if not conn_wrapper.is_valid():
                    await self._close_wrapper(conn_wrapper)
                    self._size -= 1
                    continue
                
                # 检查空闲时间
                if conn_wrapper.idle_time() * 1000 > self._max_idle_ms:
                    await self._close_wrapper(conn_wrapper)
                    self._size -= 1
                    continue
                
                self._in_use.add(conn_wrapper)
                return conn_wrapper
            
            # 创建新连接
            if self._size < self._max_size:
                conn = await self._factory()
                wrapper = Connection(
                    conn, self._factory, self._validate, self._close
                )
                self._size += 1
                self._in_use.add(wrapper)
                return wrapper
            
            # 等待连接
            raise RuntimeError("Connection pool exhausted")
    
    async def release(self, conn: Connection[T]) -> None:
        """释放连接"""
        async with self._lock:
            if conn not in self._in_use:
                return
            
            self._in_use.remove(conn)
            
            # 检查是否应该关闭
            if (conn.age() * 1000 > self._max_lifetime_ms or
                not conn.is_valid()):
                await self._close_wrapper(conn)
                self._size -= 1
                return
            
            # 放回池中
            self._connections.append(conn)
    
    async def _close_wrapper(self, wrapper: Connection[T]) -> None:
        """关闭包装器"""
        try:
            wrapper.close()
        except Exception:
            pass
    
    async def clear(self) -> None:
        """清空连接池"""
        async with self._lock:
            for conn in self._connections:
                conn.close()
            self._connections.clear()
            
            for conn in self._in_use:
                conn.close()
            self._in_use.clear()
            
            self._size = 0
    
    @property
    def stats(self) -> dict:
        """统计信息"""
        return {
            "total": self._size,
            "available": len(self._connections),
            "in_use": len(self._in_use),
            "max_size": self._max_size,
        }


# 导出
__all__ = [
    "Connection",
    "ConnectionPool",
]
