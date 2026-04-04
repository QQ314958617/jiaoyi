"""
Assert - 断言工具
基于 Claude Code assert.ts 设计

断言和异常工具。
"""
from typing import Any, Optional


class AssertionError(Exception):
    """断言错误"""
    pass


def assert_true(condition: bool, message: str = None) -> None:
    """断言为真"""
    if not condition:
        raise AssertionError(message or "Expected true, got false")


def assert_false(condition: bool, message: str = None) -> None:
    """断言为假"""
    if condition:
        raise AssertionError(message or "Expected false, got true")


def assert_equal(actual: Any, expected: Any, message: str = None) -> None:
    """断言相等"""
    if actual != expected:
        msg = message or f"Expected {expected}, got {actual}"
        raise AssertionError(msg)


def assert_not_equal(actual: Any, expected: Any, message: str = None) -> None:
    """断言不相等"""
    if actual == expected:
        raise AssertionError(message or f"Expected not {expected}")


def assert_none(value: Any, message: str = None) -> None:
    """断言为None"""
    if value is not None:
        raise AssertionError(message or f"Expected None, got {value}")


def assert_not_none(value: Any, message: str = None) -> None:
    """断言不为None"""
    if value is None:
        raise AssertionError(message or "Expected not None")


def assert_type(value: Any, expected_type: type, message: str = None) -> None:
    """断言类型"""
    if not isinstance(value, expected_type):
        msg = message or f"Expected {expected_type.__name__}, got {type(value).__name__}"
        raise AssertionError(msg)


def assert_in(value: Any, container: Any, message: str = None) -> None:
    """断言在容器中"""
    if value not in container:
        msg = message or f"Expected {value} to be in {container}"
        raise AssertionError(msg)


def assert_not_in(value: Any, container: Any, message: str = None) -> None:
    """断言不在容器中"""
    if value in container:
        raise AssertionError(message or f"Expected {value} to not be in {container}")


def assert_empty(value: Any, message: str = None) -> None:
    """断言为空"""
    if value:
        raise AssertionError(message or "Expected empty, got truthy value")


def assert_not_empty(value: Any, message: str = None) -> None:
    """断言不为空"""
    if not value:
        raise AssertionError(message or "Expected not empty")


def assert_raise(func, *args, **kwargs) -> None:
    """断言抛出异常"""
    try:
        func(*args, **kwargs)
        raise AssertionError(f"Expected {func} to raise an exception")
    except AssertionError:
        raise
    except Exception:
        pass  # 预期异常


def assert_match(value: str, pattern: str, message: str = None) -> None:
    """断言匹配正则"""
    import re
    if not re.match(pattern, value):
        msg = message or f"Expected {value} to match {pattern}"
        raise AssertionError(msg)


def invariant(condition: bool, message: str = None) -> None:
    """
    不变式断言
    
    失败时抛出AssertionError
    """
    if not condition:
        raise AssertionError(message or "Invariant violated")


# 导出
__all__ = [
    "AssertionError",
    "assert_true",
    "assert_false",
    "assert_equal",
    "assert_not_equal",
    "assert_none",
    "assert_not_none",
    "assert_type",
    "assert_in",
    "assert_not_in",
    "assert_empty",
    "assert_not_empty",
    "assert_raise",
    "assert_match",
    "invariant",
]
