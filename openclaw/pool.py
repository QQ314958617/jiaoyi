"""
Pool - 连接池
基于 Claude Code pool.ts 设计

通用对象池。
"""
from typing import Any, Callable, List


class Pool:
    """
    对象池
    
    复用对象减少分配开销。
    """
    
    def __init__(self, factory: Callable, max_size: int = 10):
        """
        Args:
            factory: 对象工厂函数
            max_size: 最大池大小
        """
        self._factory = factory
        self._max_size = max_size
        self._pool: List[Any] = []
        self._size = 0
    
    def acquire(self) -> Any:
        """
        获取对象
        
        Returns:
            对象
        """
        if self._pool:
            return self._pool.pop()
        return self._factory()
    
    def release(self, obj: Any) -> None:
        """
        释放对象回池
        
        Args:
            obj: 对象
        """
        if self._size < self._max_size:
            self._pool.append(obj)
            self._size += 1
    
    def clear(self) -> None:
        """清空池"""
        self._pool.clear()
        self._size = 0
    
    @property
    def available(self) -> int:
        """可用对象数"""
        return len(self._pool)
    
    @property
    def total(self) -> int:
        """总对象数"""
        return self._size


class ConnectionPool(Pool):
    """
    连接池
    
    专为数据库连接等资源设计。
    """
    
    def __init__(self, factory: Callable, max_size: int = 10, validator: Callable = None):
        """
        Args:
            factory: 连接工厂函数
            max_size: 最大连接数
            validator: 连接验证函数
        """
        super().__init__(factory, max_size)
        self._validator = validator or (lambda x: True)
        self._used: List[Any] = []
    
    def acquire(self) -> Any:
        """获取连接"""
        # 先尝试从池中获取
        conn = super().acquire()
        
        # 验证连接
        if not self._validator(conn):
            # 重新创建
            conn = self._factory()
        
        self._used.append(conn)
        return conn
    
    def release(self, conn: Any) -> None:
        """释放连接"""
        if conn in self._used:
            self._used.remove(conn)
        
        if self._validator(conn):
            super().release(conn)
    
    def close_all(self) -> None:
        """关闭所有连接"""
        self._used.clear()
        self.clear()


# 导出
__all__ = [
    "Pool",
    "ConnectionPool",
]
