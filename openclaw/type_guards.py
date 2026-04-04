"""
Type Guards - 类型守卫
基于 Claude Code typeGuards.ts 设计

类型守卫函数。
"""
from typing import Any, Dict, List, Optional, Union


def is_string(value: Any) -> bool:
    """检查是否为字符串"""
    return isinstance(value, str)


def is_number(value: Any) -> bool:
    """检查是否为数字"""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_integer(value: Any) -> bool:
    """检查是否为整数"""
    return isinstance(value, int) and not isinstance(value, bool)


def is_boolean(value: Any) -> bool:
    """检查是否为布尔值"""
    return isinstance(value, bool)


def is_list(value: Any) -> bool:
    """检查是否为列表"""
    return isinstance(value, list)


def is_dict(value: Any) -> bool:
    """检查是否为字典"""
    return isinstance(value, dict)


def is_none(value: Any) -> bool:
    """检查是否为None"""
    return value is None


def is_function(value: Any) -> bool:
    """检查是否为函数"""
    return callable(value)


def is_object(value: Any) -> bool:
    """检查是否为对象（非原始类型）"""
    return value is not None and not isinstance(value, (str, int, float, bool, list, tuple))


def is_empty(value: Any) -> bool:
    """检查是否为空"""
    if value is None:
        return True
    if isinstance(value, (str, list, dict, tuple)):
        return len(value) == 0
    return False


def has_keys(obj: dict, *keys: str) -> bool:
    """检查对象是否包含指定键"""
    return all(key in obj for key in keys)


def has_value(value: Any) -> bool:
    """检查是否有值（非None）"""
    return value is not None


def is_non_empty_string(value: Any) -> bool:
    """检查是否为非空字符串"""
    return isinstance(value, str) and len(value.strip()) > 0


def is_in_range(value: int, min_val: int, max_val: int) -> bool:
    """检查数字是否在范围内"""
    return min_val <= value <= max_val


def isinstance_check(type_name: str):
    """
    创建类型检查函数
    
    Args:
        type_name: 类型名
        
    Returns:
        类型检查函数
    """
    def checker(value: Any) -> bool:
        return type(value).__name__ == type_name
    return checker


# 导出
__all__ = [
    "is_string",
    "is_number",
    "is_integer",
    "is_boolean",
    "is_list",
    "is_dict",
    "is_none",
    "is_function",
    "is_object",
    "is_empty",
    "has_keys",
    "has_value",
    "is_non_empty_string",
    "is_in_range",
    "isinstance_check",
]
