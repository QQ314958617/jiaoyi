"""
Operator - 操作符
基于 Claude Code operator.ts 设计

操作符函数。
"""
from typing import Any, Callable


def identity(x: Any) -> Any:
    """恒等函数"""
    return x


def constant(x: Any) -> Callable:
    """常量函数"""
    return lambda *args, **kwargs: x


def negate(fn: Callable) -> Callable:
    """取反"""
    return lambda *args, **kwargs: not fn(*args, **kwargs)


def property_(name: str) -> Callable:
    """获取属性"""
    return lambda obj: getattr(obj, name, None)


def method(name: str) -> Callable:
    """调用方法"""
    def caller(obj, *args, **kwargs):
        return getattr(obj, name)(*args, **kwargs)
    return caller


def eq(value: Any) -> Callable:
    """等于"""
    return lambda x: x == value


def ne(value: Any) -> Callable:
    """不等于"""
    return lambda x: x != value


def gt(value: Any) -> Callable:
    """大于"""
    return lambda x: x > value


def lt(value: Any) -> Callable:
    """小于"""
    return lambda x: x < value


def gte(value: Any) -> Callable:
    """大于等于"""
    return lambda x: x >= value


def lte(value: Any) -> Callable:
    """小于等于"""
    return lambda x: x <= value


def is_none(value: Any) -> bool:
    """是否为None"""
    return value is None


def is_not_none(value: Any) -> bool:
    """是否不为None"""
    return value is not None


def add(a: Any, b: Any) -> Any:
    """加法"""
    return a + b


def subtract(a: Any, b: Any) -> Any:
    """减法"""
    return a - b


def multiply(a: Any, b: Any) -> Any:
    """乘法"""
    return a * b


def divide(a: Any, b: Any) -> Any:
    """除法"""
    return a / b


def modulo(a: Any, b: Any) -> Any:
    """取模"""
    return a % b


def power(a: Any, b: Any) -> Any:
    """幂"""
    return a ** b


# 导出
__all__ = [
    "identity",
    "constant",
    "negate",
    "property_",
    "method",
    "eq",
    "ne",
    "gt",
    "lt",
    "gte",
    "lte",
    "is_none",
    "is_not_none",
    "add",
    "subtract",
    "multiply",
    "divide",
    "modulo",
    "power",
]
