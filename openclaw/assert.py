"""
Assert - 断言
基于 Claude Code assert.ts 设计

断言工具。
"""


class AssertionError(Exception):
    """断言错误"""
    pass


def assert_(condition: bool, message: str = "Assertion failed"):
    """断言条件为真"""
    if not condition:
        raise AssertionError(message)


def assert_equal(actual: any, expected: any, message: str = None):
    """断言相等"""
    if actual != expected:
        msg = message or f"{actual!r} != {expected!r}"
        raise AssertionError(msg)


def assert_not_equal(actual: any, expected: any, message: str = None):
    """断言不相等"""
    if actual == expected:
        msg = message or f"{actual!r} == {expected!r}"
        raise AssertionError(msg)


def assert_true(value: any, message: str = None):
    """断言为真"""
    if not value:
        msg = message or f"{value!r} is not truthy"
        raise AssertionError(msg)


def assert_false(value: any, message: str = None):
    """断言为假"""
    if value:
        msg = message or f"{value!r} is not falsy"
        raise AssertionError(msg)


def assert_none(value: any, message: str = None):
    """断言为None"""
    if value is not None:
        msg = message or f"{value!r} is not None"
        raise AssertionError(msg)


def assert_not_none(value: any, message: str = None):
    """断言不为None"""
    if value is None:
        msg = message or "value is None"
        raise AssertionError(msg)


def assert_raises(fn: callable, *args, **kwargs):
    """断言抛出异常"""
    try:
        fn(*args, **kwargs)
        raise AssertionError("Expected exception was not raised")
    except Exception:
        pass  # Expected


def assert_type(value: any, type_: type, message: str = None):
    """断言类型"""
    if not isinstance(value, type_):
        msg = message or f"{type(value).__name__} is not {type_.__name__}"
        raise AssertionError(msg)


# 导出
__all__ = [
    "AssertionError",
    "assert_",
    "assert_equal",
    "assert_not_equal",
    "assert_true",
    "assert_false",
    "assert_none",
    "assert_not_none",
    "assert_raises",
    "assert_type",
]
