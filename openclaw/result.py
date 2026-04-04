"""
Result - 结果
基于 Claude Code result.ts 设计

结果类型工具。
"""
from typing import Any, Callable, TypeVar

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


class Result:
    """
    结果类型
    
    表示成功或失败。
    """
    
    def __init__(self, value: Any = None, error: Any = None):
        """
        Args:
            value: 成功值
            error: 错误
        """
        self._value = value
        self._error = error
        self._success = error is None
    
    @classmethod
    def ok(cls, value: T = None) -> "Result[T, None]":
        """创建成功结果"""
        return cls(value=value, error=None)
    
    @classmethod
    def err(cls, error: E) -> "Result[None, E]":
        """创建错误结果"""
        return cls(value=None, error=error)
    
    @property
    def success(self) -> bool:
        """是否成功"""
        return self._success
    
    @property
    def failure(self) -> bool:
        """是否失败"""
        return not self._success
    
    def get(self) -> T:
        """获取成功值"""
        if self._success:
            return self._value
        raise ValueError(f"Result is failure: {self._error}")
    
    def get_error(self) -> E:
        """获取错误"""
        if self._success:
            raise ValueError("Result is success")
        return self._error
    
    def or_else(self, default: T) -> T:
        """成功返回值，失败返回默认值"""
        return self._value if self._success else default
    
    def map(self, mapper: Callable[[T], U]) -> "Result[U, E]":
        """映射成功值"""
        if self._success:
            return Result.ok(mapper(self._value))
        return Result.err(self._error)
    
    def flat_map(self, mapper: Callable[[T], "Result"]) -> "Result":
        """扁平映射"""
        if self._success:
            return mapper(self._value)
        return Result.err(self._error)
    
    def map_error(self, mapper: Callable[[E], Any]) -> "Result[T, Any]":
        """映射错误"""
        if self._success:
            return Result.ok(self._value)
        return Result.err(mapper(self._error))
    
    def is_ok(self) -> bool:
        """是否成功"""
        return self._success
    
    def is_err(self) -> bool:
        """是否失败"""
        return not self._success
    
    def if_ok(self, consumer: Callable[[T], None]) -> None:
        """如果成功则执行"""
        if self._success:
            consumer(self._value)
    
    def if_err(self, consumer: Callable[[E], None]) -> None:
        """如果失败则执行"""
        if not self._success:
            consumer(self._error)
    
    def __bool__(self) -> bool:
        return self._success
    
    def __repr__(self) -> str:
        if self._success:
            return f"Result.ok({self._value!r})"
        return f"Result.err({self._error!r})"


def result(value: T = None, error: Any = None) -> Result:
    """
    创建Result
    
    Args:
        value: 成功值
        error: 错误
        
    Returns:
        Result实例
    """
    return Result(value, error)


def from_call(func: Callable, *args, **kwargs) -> Result:
    """
    从函数调用创建Result
    
    Args:
        func: 函数
        *args, **kwargs: 函数参数
        
    Returns:
        Result实例
    """
    try:
        return Result.ok(func(*args, **kwargs))
    except Exception as e:
        return Result.err(e)


def from_call_no_raise(func: Callable, *args, **kwargs) -> Result:
    """from_call的别名"""
    return from_call(func, *args, **kwargs)


# 导出
__all__ = [
    "Result",
    "result",
    "from_call",
    "from_call_no_raise",
]
