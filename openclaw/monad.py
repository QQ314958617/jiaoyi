"""
Monad - 单子
基于 Claude Code monad.ts 设计

函数式单子工具。
"""
from typing import Any, Callable, Generic, TypeVar

T = TypeVar('T')
U = TypeVar('U')


class Maybe(Generic[T]):
    """
    Maybe单子
    
    表示可能存在或不存在的值。
    """
    
    def __init__(self, value: Any = None):
        self._value = value
        self._present = value is not None
    
    @classmethod
    def just(cls, value: T) -> "Maybe[T]":
        """创建有值的Maybe"""
        return cls(value)
    
    @classmethod
    def nothing(cls) -> "Maybe":
        """创建空Maybe"""
        return cls(None)
    
    @property
    def is_present(self) -> bool:
        return self._present
    
    def get(self) -> T:
        """获取值"""
        if not self._present:
            raise ValueError("No value")
        return self._value
    
    def or_else(self, default: T) -> T:
        """获取值或默认值"""
        return self._value if self._present else default
    
    def map(self, fn: Callable[[T], U]) -> "Maybe[U]":
        """映射"""
        if not self._present:
            return Maybe.nothing()
        return Maybe.just(fn(self._value))
    
    def flat_map(self, fn: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        """扁平映射"""
        if not self._present:
            return Maybe.nothing()
        return fn(self._value)
    
    def filter(self, predicate: Callable[[T], bool]) -> "Maybe[T]":
        """过滤"""
        if self._present and predicate(self._value):
            return self
        return Maybe.nothing()


class Either(Generic[T, U]):
    """
    Either单子
    
    表示两种可能的结果。
    """
    
    def __init__(self, left: Any = None, right: Any = None, is_left: bool = True):
        self._left = left
        self._right = right
        self._is_left = is_left
    
    @classmethod
    def left(cls, value: T) -> "Either[T, U]":
        """创建Left"""
        return cls(left=value, is_left=True)
    
    @classmethod
    def right(cls, value: U) -> "Either[T, U]":
        """创建Right"""
        return cls(right=value, is_left=False)
    
    @property
    def is_left(self) -> bool:
        return self._is_left
    
    @property
    def is_right(self) -> bool:
        return not self._is_left
    
    def get_left(self) -> T:
        """获取Left值"""
        if self._is_left:
            return self._left
        raise ValueError("Not left")
    
    def get_right(self) -> U:
        """获取Right值"""
        if not self._is_left:
            return self._right
        raise ValueError("Not right")
    
    def map_left(self, fn: Callable[[T], Any]) -> "Either":
        """映射Left"""
        if self._is_left:
            return Either.left(fn(self._left))
        return self
    
    def map_right(self, fn: Callable[[U], Any]) -> "Either":
        """映射Right"""
        if not self._is_left:
            return Either.right(fn(self._right))
        return self
    
    def flat_map(self, fn: Callable) -> "Either":
        """扁平映射"""
        if self._is_left:
            return self
        return fn(self._right)


class IO:
    """
    IO单子
    
    延迟执行副作用。
    """
    
    def __init__(self, fn: Callable):
        self._fn = fn
    
    @classmethod
    def of(cls, value: Any) -> "IO":
        """创建纯IO"""
        return cls(lambda: value)
    
    def run(self) -> Any:
        """执行"""
        return self._fn()
    
    def map(self, fn: Callable) -> "IO":
        """映射"""
        return IO(lambda: fn(self._fn()))
    
    def flat_map(self, fn: Callable) -> "IO":
        """扁平映射"""
        return IO(lambda: fn(self._fn()).run())


# 导出
__all__ = [
    "Maybe",
    "Either",
    "IO",
]
