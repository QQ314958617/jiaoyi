"""
Assert2 - 断言
基于 Claude Code assert.ts 设计

断言工具。
"""
from typing import Any, Optional


class AssertionError(Exception):
    """断言错误"""
    pass


def assert_(condition: bool, message: str = "Assertion failed") -> None:
    """
    断言
    
    Args:
        condition: 条件
        message: 错误信息
        
    Raises:
        AssertionError: 条件为False时
    """
    if not condition:
        raise AssertionError(message)


def assert_eq(actual: Any, expected: Any, message: str = None) -> None:
    """
    断言相等
    
    Args:
        actual: 实际值
        expected: 期望值
        message: 错误信息
    """
    if actual != expected:
        msg = message or f"Expected {expected!r}, got {actual!r}"
        raise AssertionError(msg)


def assert_ne(actual: Any, expected: Any, message: str = None) -> None:
    """
    断言不等
    
    Args:
        actual: 实际值
        expected: 不期望的值
        message: 错误信息
    """
    if actual == expected:
        msg = message or f"Expected not {expected!r}"
        raise AssertionError(msg)


def assert_none(value: Any, message: str = None) -> None:
    """断言为None"""
    if value is not None:
        msg = message or f"Expected None, got {value!r}"
        raise AssertionError(msg)


def assert_not_none(value: Any, message: str = None) -> None:
    """断言不为None"""
    if value is None:
        msg = message or "Expected not None"
        raise AssertionError(msg)


def assert_type(value: Any, expected_type: type, message: str = None) -> None:
    """断言类型"""
    if not isinstance(value, expected_type):
        msg = message or f"Expected type {expected_type.__name__}, got {type(value).__name__}"
        raise AssertionError(msg)


def assert_in(value: Any, container: Any, message: str = None) -> None:
    """断言在容器中"""
    if value not in container:
        msg = message or f"{value!r} not in {container!r}"
        raise AssertionError(msg)


def assert_between(value: Any, min_val: Any, max_val: Any, message: str = None) -> None:
    """断言在范围内"""
    if not (min_val <= value <= max_val):
        msg = message or f"{value!r} not between {min_val!r} and {max_val!r}"
        raise AssertionError(msg)


def assert_empty(value: Any, message: str = None) -> None:
    """断言为空"""
    if value:
        msg = message or f"Expected empty, got {value!r}"
        raise AssertionError(msg)


def assert_not_empty(value: Any, message: str = None) -> None:
    """断言不为空"""
    if not value:
        msg = message or "Expected not empty"
        raise AssertionError(msg)


# 导出
__all__ = [
    "AssertionError",
    "assert_",
    "assert_eq",
    "assert_ne",
    "assert_none",
    "assert_not_none",
    "assert_type",
    "assert_in",
    "assert_between",
    "assert_empty",
    "assert_not_empty",
]
