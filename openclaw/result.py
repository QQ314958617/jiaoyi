"""
Result Type - 结果类型
基于 Claude Code result.ts 设计

Rust风格的Result类型用于错误处理。
"""
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Optional

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


@dataclass
class Ok(Generic[T]):
    """成功结果"""
    value: T
    
    def is_ok(self) -> bool:
        return True
    
    def is_err(self) -> bool:
        return False
    
    def unwrap(self) -> T:
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        return self.value
    
    def map(self, fn: Callable[[T], U]) -> "Ok[U]":
        return Ok(fn(self.value))
    
    def map_err(self, fn: Callable) -> "Ok[T]":
        return self
    
    def and_then(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return fn(self.value)


@dataclass
class Err(Generic[E]):
    """错误结果"""
    error: E
    
    def is_ok(self) -> bool:
        return False
    
    def is_err(self) -> bool:
        return True
    
    def unwrap(self) -> T:
        raise self.error
    
    def unwrap_or(self, default: T) -> T:
        return default
    
    def map(self, fn: Callable) -> "Err[E]":
        return self
    
    def map_err(self, fn: Callable[[E], U]) -> "Err[U]":
        return Err(fn(self.error))
    
    def and_then(self, fn: Callable) -> "Err[E]":
        return self


Result = Ok[T] | Err[E]


def ok(value: T) -> Ok[T]:
    """创建成功结果"""
    return Ok(value)


def err(error: E) -> Err[E]:
    """创建错误结果"""
    return Err(error)


def from_optional(
    value: Optional[T],
    error: E,
) -> Result[T, E]:
    """
    从Optional创建Result
    
    Args:
        value: 可选值
        error: 错误值
        
    Returns:
        Result
    """
    if value is None:
        return Err(error)
    return Ok(value)


def fromCallable(fn: Callable[[], T], *args, **kwargs) -> Result[T, Exception]:
    """
    从函数创建Result
    
    Args:
        fn: 函数
        *args, **kwargs: 函数参数
        
    Returns:
        Result
    """
    try:
        return Ok(fn(*args, **kwargs))
    except Exception as e:
        return Err(e)


# 导出
__all__ = [
    "Ok",
    "Err",
    "Result",
    "ok",
    "err",
    "from_optional",
    "fromCallable",
]
