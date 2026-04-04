"""
Ref - 引用
基于 Claude Code ref.ts 设计

引用类型工具。
"""
from typing import Any, Callable, Generic, TypeVar

T = TypeVar('T')


class Ref(Generic[T]):
    """
    引用类型
    
    可变容器。
    """
    
    def __init__(self, value: T):
        """
        Args:
            value: 初始值
        """
        self._value = value
    
    @property
    def value(self) -> T:
        """获取值"""
        return self._value
    
    @value.setter
    def value(self, new_value: T) -> None:
        """设置值"""
        self._value = new_value
    
    def get(self) -> T:
        """获取值"""
        return self._value
    
    def set(self, new_value: T) -> None:
        """设置值"""
        self._value = new_value
    
    def update(self, fn: Callable[[T], T]) -> T:
        """
        更新值
        
        Args:
            fn: 更新函数
            
        Returns:
            新值
        """
        self._value = fn(self._value)
        return self._value
    
    def __repr__(self) -> str:
        return f"Ref({self._value!r})"
    
    def __str__(self) -> str:
        return str(self._value)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Ref):
            return self._value == other._value
        return self._value == other


class MutableRef(Ref[T]):
    """
    可变引用
    
    支持解引用赋值。
    """
    pass


def ref(value: T) -> Ref[T]:
    """
    创建引用
    
    Args:
        value: 初始值
        
    Returns:
        Ref实例
    """
    return Ref(value)


def deref(ref_instance: Ref) -> Any:
    """
    解引用
    
    Args:
        ref_instance: Ref实例
        
    Returns:
        值
    """
    return ref_instance.value if isinstance(ref_instance, Ref) else ref_instance


class RefComputation:
    """
    引用计算
    
    基于依赖自动更新。
    """
    
    def __init__(self, fn: Callable, *refs: Ref):
        """
        Args:
            fn: 计算函数
            *refs: 依赖的引用
        """
        self._fn = fn
        self._refs = refs
        self._cached = None
    
    def get(self) -> Any:
        """获取计算值"""
        values = [r.value for r in self._refs]
        self._cached = self._fn(*values)
        return self._cached


# 导出
__all__ = [
    "Ref",
    "MutableRef",
    "ref",
    "deref",
    "RefComputation",
]
