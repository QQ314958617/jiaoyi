"""
Option Type - Option类型
基于 Claude Code option.ts 设计

Rust风格的Option类型。
"""
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar('T')
U = TypeVar('U')


@dataclass
class Some(Generic[T]):
    """有值"""
    value: T
    
    def is_some(self) -> bool:
        return True
    
    def is_none(self) -> bool:
        return False
    
    def unwrap(self) -> T:
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        return self.value
    
    def map(self, fn: Callable[[T], U]) -> "Some[U]":
        return Some(fn(self.value))
    
    def and_then(self, fn: Callable[[T], "Option[U]"]) -> "Option[U]":
        return fn(self.value)
    
    def filter(self, pred: Callable[[T], bool]) -> "Option[T]":
        if pred(self.value):
            return self
        return NOTHING


@dataclass 
class Nothing:
    """无值"""
    
    def is_some(self) -> bool:
        return False
    
    def is_none(self) -> bool:
        return True
    
    def unwrap(self) -> T:
        raise ValueError("Called unwrap on Nothing")
    
    def unwrap_or(self, default: T) -> T:
        return default
    
    def map(self, fn: Callable) -> "Nothing":
        return self
    
    def and_then(self, fn: Callable) -> "Nothing":
        return self
    
    def filter(self, pred: Callable) -> "Nothing":
        return self


Option = Some[T] | Nothing
NOTHING = Nothing()


def some(value: T) -> Some[T]:
    """创建Some"""
    return Some(value)


def nothing() -> Nothing:
    """创建Nothing"""
    return NOTHING


def from_nullable(value) -> Option:
    """从可空值创建Option"""
    if value is None:
        return NOTHING
    return Some(value)


# 导出
__all__ = [
    "Some",
    "Nothing",
    "Option",
    "NOTHING",
    "some",
    "nothing",
    "from_nullable",
]
