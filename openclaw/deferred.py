"""
Deferred - 延迟计算
基于 Claude Code deferred.ts 设计

延迟计算值的工具。
"""
from typing import Callable, Generic, TypeVar, Optional

T = TypeVar('T')


class Deferred(Generic[T]):
    """
    延迟计算值
    
    值在首次访问时才计算，之后缓存结果。
    """
    
    def __init__(self, factory: Callable[[], T]):
        """
        Args:
            factory: 值工厂函数
        """
        self._factory = factory
        self._value: Optional[T] = None
        self._computed = False
    
    def get(self) -> T:
        """
        获取值（惰性计算）
        
        Returns:
            计算后的值
        """
        if not self._computed:
            self._value = self._factory()
            self._computed = True
        return self._value
    
    @property
    def value(self) -> T:
        """属性访问器"""
        return self.get()
    
    def is_computed(self) -> bool:
        """是否已计算"""
        return self._computed
    
    def reset(self) -> None:
        """重置缓存"""
        self._value = None
        self._computed = False


def deferred(factory: Callable[[], T]) -> Deferred[T]:
    """
    创建延迟计算值
    
    Args:
        factory: 值工厂函数
        
    Returns:
        Deferred对象
    """
    return Deferred(factory)


class Lazy(Generic[T]):
    """
    更简单的惰性值包装
    
    使用描述符协议实现。
    """
    
    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._value: Optional[T] = None
    
    def __get__(self, obj, objtype=None) -> T:
        if self._value is None:
            self._value = self._factory()
        return self._value


# 导出
__all__ = [
    "Deferred",
    "deferred",
    "Lazy",
]
