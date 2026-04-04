"""
MessagePredicates - 消息断言
基于 Claude Code message_predicates.ts 设计

消息断言工具。
"""
from typing import Any, Callable, List, Optional


def is_empty(value: Any) -> bool:
    """是否为空"""
    if value is None:
        return True
    if isinstance(value, (str, list, dict, tuple, set)):
        return len(value) == 0
    return False


def is_not_empty(value: Any) -> bool:
    """是否不为空"""
    return not is_empty(value)


def equals(expected: Any) -> Callable:
    """等于"""
    return lambda actual: actual == expected


def not_equals(expected: Any) -> Callable:
    """不等于"""
    return lambda actual: actual != expected


def contains(substr: str) -> Callable:
    """包含"""
    return lambda text: substr in str(text)


def matches(pattern: str) -> Callable:
    """正则匹配"""
    import re
    compiled = re.compile(pattern)
    return lambda text: bool(compiled.search(str(text)))


def starts_with(prefix: str) -> Callable:
    """开头"""
    return lambda text: str(text).startswith(prefix)


def ends_with(suffix: str) -> Callable:
    """结尾"""
    return lambda text: str(text).endswith(suffix)


def has_length(length: int) -> Callable:
    """长度为"""
    return lambda text: len(text) == length


def has_min_length(min_length: int) -> Callable:
    """最小长度"""
    return lambda text: len(text) >= min_length


def has_max_length(max_length: int) -> Callable:
    """最大长度"""
    return lambda text: len(text) <= max_length


def is_type(type_: type) -> Callable:
    """类型检查"""
    return lambda value: isinstance(value, type_)


def is_in(*choices) -> Callable:
    """在列表中"""
    return lambda value: value in choices


def satisfies(predicate: Callable) -> Callable:
    """满足条件"""
    return lambda value: predicate(value)


class MessagePredicate:
    """消息断言"""
    
    def __init__(self, predicate: Callable, message: str = None):
        self._predicate = predicate
        self._message = message or "Predicate failed"
    
    def test(self, value: Any) -> bool:
        """测试"""
        return self._predicate(value)
    
    def __call__(self, value: Any) -> bool:
        return self.test(value)


def assert_predicate(value: Any, predicate: Callable, message: str = None) -> bool:
    """
    断言
    
    Raises:
        AssertionError: 如果断言失败
    """
    if not predicate(value):
        raise AssertionError(message or f"Assertion failed: {value}")
    return True


# 导出
__all__ = [
    "is_empty",
    "is_not_empty",
    "equals",
    "not_equals",
    "contains",
    "matches",
    "starts_with",
    "ends_with",
    "has_length",
    "has_min_length",
    "has_max_length",
    "is_type",
    "is_in",
    "satisfies",
    "MessagePredicate",
    "assert_predicate",
]
