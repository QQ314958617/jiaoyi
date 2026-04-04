"""
Deferred - 延迟对象
基于 Claude Code deferred.ts 设计

延迟计算工具。
"""
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')


class Deferred:
    """
    延迟对象
    
    延迟到首次访问时才计算值。
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
        """获取值（延迟计算）"""
        if not self._computed:
            self._value = self._factory()
            self._computed = True
        return self._value
    
    @property
    def value(self) -> T:
        """属性访问"""
        return self.get()
    
    def is_computed(self) -> bool:
        """是否已计算"""
        return self._computed
    
    def reset(self) -> None:
        """重置（下次访问重新计算）"""
        self._computed = False
        self._value = None


class Lazy:
    """
    惰性计算包装器
    """
    
    def __init__(self, factory: Callable[[], T]):
        self._factory = factory
        self._value: Optional[T] = None
        self._initialized = False
    
    def get(self) -> T:
        """获取值"""
        if not self._initialized:
            self._value = self._factory()
            self._initialized = True
        return self._value
    
    def __call__(self) -> T:
        return self.get()
    
    @property
    def value(self) -> T:
        return self.get()
    
    def reset(self) -> None:
        """重置"""
        self._initialized = False
        self._value = None


def lazy(factory: Callable[[], T]) -> Lazy[T]:
    """
    创建惰性值
    
    Args:
        factory: 工厂函数
        
    Returns:
        Lazy实例
    """
    return Lazy(factory)


class LazyDict:
    """
    惰性字典
    
    值延迟计算。
    """
    
    def __init__(self, factory_map: dict = None):
        """
        Args:
            factory_map: {key: factory} 映射
        """
        self._factories = factory_map or {}
        self._values: dict = {}
        self._computed: set = set()
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取值"""
        if key in self._computed:
            return self._values.get(key, default)
        
        if key in self._factories:
            self._values[key] = self._factories[key]()
            self._computed.add(key)
            return self._values[key]
        
        return default
    
    def set(self, key: str, value: Any) -> None:
        """设置值（直接值，不延迟）"""
        self._values[key] = value
        self._computed.add(key)
    
    def has(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._factories or key in self._values
    
    def computed(self, key: str) -> bool:
        """是否已计算"""
        return key in self._computed
    
    def reset(self, key: str = None) -> None:
        """重置"""
        if key is None:
            self._values.clear()
            self._computed.clear()
        elif key in self._computed:
            del self._values[key]
            self._computed.remove(key)


# 导出
__all__ = [
    "Deferred",
    "Lazy",
    "lazy",
    "LazyDict",
]
