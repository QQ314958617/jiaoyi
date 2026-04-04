"""
Strict - 严格模式
基于 Claude Code strict.ts 设计

严格类型检查和验证。
"""
from typing import Any, Callable, TypeVar

T = TypeVar('T')


class ValidationError(Exception):
    """验证错误"""
    
    def __init__(self, message: str, path: str = ""):
        self.message = message
        self.path = path
        super().__init__(f"{path}: {message}" if path else message)


def assert_type(expected_type: type) -> Callable:
    """
    类型断言装饰器
    
    Args:
        expected_type: 期望类型
        
    Returns:
        装饰器
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(value: Any) -> Any:
            if not isinstance(value, expected_type):
                raise ValidationError(
                    f"Expected {expected_type.__name__}, got {type(value).__name__}"
                )
            return value
        return wrapper
    return decorator


def assert_not_none(func: Callable) -> Callable:
    """断言非空"""
    def wrapper(value: Any) -> Any:
        if value is None:
            raise ValidationError("Value cannot be None")
        return func(value)
    return wrapper


def assert_not_empty(func: Callable) -> Callable:
    """断言非空（字符串/列表）"""
    def wrapper(value: Any) -> Any:
        if value is None or (hasattr(value, '__len__') and len(value) == 0):
            raise ValidationError("Value cannot be empty")
        return func(value)
    return wrapper


def assert_range(min_val: float = None, max_val: float = None) -> Callable:
    """
    范围断言
    
    Args:
        min_val: 最小值
        max_val: 最大值
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(value: Any) -> Any:
            if min_val is not None and value < min_val:
                raise ValidationError(f"Value must be >= {min_val}")
            if max_val is not None and value > max_val:
                raise ValidationError(f"Value must be <= {max_val}")
            return value
        return wrapper
    return decorator


def assert_length(min_len: int = None, max_len: int = None) -> Callable:
    """
    长度断言
    
    Args:
        min_len: 最小长度
        max_len: 最大长度
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(value: Any) -> Any:
            length = len(value)
            if min_len is not None and length < min_len:
                raise ValidationError(f"Length must be >= {min_len}")
            if max_len is not None and length > max_len:
                raise ValidationError(f"Length must be <= {max_len}")
            return value
        return wrapper
    return decorator


def assert_pattern(pattern: str) -> Callable:
    """
    正则断言
    
    Args:
        pattern: 正则模式
    """
    import re
    compiled = re.compile(pattern)
    
    def decorator(func: Callable) -> Callable:
        def wrapper(value: str) -> str:
            if not compiled.match(value):
                raise ValidationError(f"Value does not match pattern: {pattern}")
            return value
        return wrapper
    return decorator


class Strict:
    """
    严格模式上下文
    
    启用时进行严格检查。
    """
    
    _enabled = False
    
    @classmethod
    def enable(cls) -> None:
        """启用严格模式"""
        cls._enabled = True
    
    @classmethod
    def disable(cls) -> None:
        """禁用严格模式"""
        cls._enabled = False
    
    @classmethod
    def is_enabled(cls) -> bool:
        """是否启用"""
        return cls._enabled


# 导出
__all__ = [
    "ValidationError",
    "assert_type",
    "assert_not_none",
    "assert_not_empty",
    "assert_range",
    "assert_length",
    "assert_pattern",
    "Strict",
]
