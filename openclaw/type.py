"""
Type - 类型
基于 Claude Code type.ts 设计

类型工具。
"""
from typing import Any, get_origin, get_args


def is_defined(value: Any) -> bool:
    """是否为非None定义"""
    return value is not None


def is_undefined(value: Any) -> bool:
    """是否为Undefined"""
    return value is None


def is_null(value: Any) -> bool:
    """是否为Null"""
    return value is None


def is_number(value: Any) -> bool:
    """是否为数字"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_string(value: Any) -> bool:
    """是否为字符串"""
    return isinstance(value, str)


def is_boolean(value: Any) -> bool:
    """是否为布尔"""
    return isinstance(value, bool)


def is_function(value: Any) -> bool:
    """是否为函数"""
    return callable(value)


def is_array(value: Any) -> bool:
    """是否为数组"""
    return isinstance(value, list)


def is_object(value: Any) -> bool:
    """是否为对象"""
    return isinstance(value, dict)


def is_dict(value: Any) -> bool:
    """是否为字典"""
    return isinstance(value, dict)


def is_tuple(value: Any) -> bool:
    """是否为元组"""
    return isinstance(value, tuple)


def is_set(value: Any) -> bool:
    """是否为集合"""
    return isinstance(value, set)


def is_list(value: Any) -> bool:
    """是否为列表"""
    return isinstance(value, list)


def is_empty(value: Any) -> bool:
    """是否为空"""
    if value is None:
        return True
    if isinstance(value, (list, dict, tuple, set, str)):
        return len(value) == 0
    return False


def is_equal(a: Any, b: Any) -> bool:
    """是否相等"""
    if type(a) != type(b):
        return False
    if isinstance(a, dict):
        return a == b
    if isinstance(a, (list, tuple)):
        return a == b
    return a == b


def get_type(value: Any) -> str:
    """获取类型名"""
    return type(value).__name__


def is_instance(value: Any, cls: type) -> bool:
    """是否为实例"""
    return isinstance(value, cls)


def is_subclass(cls: type, base: type) -> bool:
    """是否为子类"""
    return issubclass(cls, base)


def is_promise(value: Any) -> bool:
    """是否为Promise"""
    return hasattr(value, '__await__')


def is_iterable(value: Any) -> bool:
    """是否可迭代"""
    return hasattr(value, '__iter__')


def is_async_iterable(value: Any) -> bool:
    """是否异步可迭代"""
    return hasattr(value, '__aiter__')


# 导出
__all__ = [
    "is_defined",
    "is_undefined",
    "is_null",
    "is_number",
    "is_string",
    "is_boolean",
    "is_function",
    "is_array",
    "is_object",
    "is_dict",
    "is_tuple",
    "is_set",
    "is_list",
    "is_empty",
    "is_equal",
    "get_type",
    "is_instance",
    "is_subclass",
    "is_promise",
    "is_iterable",
    "is_async_iterable",
]
