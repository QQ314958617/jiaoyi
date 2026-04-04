"""
Optional - 可选值
基于 Claude Code optional.ts 设计

可选值工具。
"""
from typing import Any, Callable, Optional, TypeVar

T = TypeVar('T')
U = TypeVar('U')


class Optional:
    """
    可选值
    
    表示可能存在或不存在的值。
    """
    
    def __init__(self, value: Any = None):
        """
        Args:
            value: 值（可为None）
        """
        self._value = value
        self._present = value is not None
    
    @classmethod
    def of(cls, value: T) -> "Optional[T]":
        """创建Optional"""
        return cls(value)
    
    @classmethod
    def empty(cls) -> "Optional":
        """创建空Optional"""
        return cls(None)
    
    @property
    def present(self) -> bool:
        """值是否存在"""
        return self._present
    
    def get(self) -> T:
        """获取值"""
        if not self._present:
            raise ValueError("No value present")
        return self._value
    
    def or_else(self, default: T) -> T:
        """获取值或默认值"""
        return self._value if self._present else default
    
    def or_else_get(self, supplier: Callable[[], T]) -> T:
        """获取值或计算默认值"""
        return self._value if self._present else supplier()
    
    def or_else_raise(self, exception: Exception) -> T:
        """获取值或抛异常"""
        if not self._present:
            raise exception
        return self._value
    
    def if_present(self, consumer: Callable[[T], None]) -> None:
        """如果存在则执行"""
        if self._present:
            consumer(self._value)
    
    def if_present_or_else(
        self,
        consumer: Callable[[T], None],
        else_action: Callable,
    ) -> None:
        """如果存在执行consumer，否则执行else_action"""
        if self._present:
            consumer(self._value)
        else:
            else_action()
    
    def map(self, mapper: Callable[[T], U]) -> "Optional[U]":
        """映射值"""
        if not self._present:
            return Optional.empty()
        
        result = mapper(self._value)
        return Optional(result)
    
    def flat_map(self, mapper: Callable[[T], "Optional[U]"]) -> "Optional[U]":
        """扁平映射"""
        if not self._present:
            return Optional.empty()
        
        return mapper(self._value)
    
    def filter(self, predicate: Callable[[T], bool]) -> "Optional[T]":
        """过滤"""
        if not self._present:
            return self
        
        if predicate(self._value):
            return self
        
        return Optional.empty()
    
    def is_empty(self) -> bool:
        """是否为空"""
        return not self._present
    
    def __bool__(self) -> bool:
        return self._present
    
    def __repr__(self) -> str:
        if self._present:
            return f"Optional({self._value!r})"
        return "Optional.empty"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Optional):
            if not self._present and not other._present:
                return True
            return self._present == other._present and self._value == other._value
        return False


def optional(value: T) -> Optional[T]:
    """
    创建Optional
    
    Args:
        value: 值
        
    Returns:
        Optional实例
    """
    return Optional.of(value)


def coalesce(*values) -> Any:
    """
    返回第一个非None值
    
    Args:
        *values: 值列表
        
    Returns:
        第一个非None值或None
    """
    for value in values:
        if value is not None:
            return value
    return None


# 导出
__all__ = [
    "Optional",
    "optional",
    "coalesce",
]
