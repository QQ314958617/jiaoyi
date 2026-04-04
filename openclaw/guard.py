"""
Guard - 类型守卫
基于 Claude Code guard.ts 设计

类型守卫工具。
"""
from typing import Any, Callable, List, Type, TypeVar

T = TypeVar('T')


def is_type(value: Any, type_or_tuple: Type or tuple) -> bool:
    """
    类型检查
    
    Args:
        value: 值
        type_or_tuple: 类型或类型元组
        
    Returns:
        是否为指定类型
    """
    return isinstance(value, type_or_tuple)


def is_nonnull(value: Any) -> bool:
    """非Null"""
    return value is not None


def is_truly(value: Any) -> bool:
    """真值"""
    return bool(value)


def is_falsy(value: Any) -> bool:
    """假值"""
    return not value


def has_property(obj: Any, prop: str) -> bool:
    """是否有属性"""
    if isinstance(obj, dict):
        return prop in obj
    return hasattr(obj, prop)


def has_key(obj: dict, key: str) -> bool:
    """是否有键"""
    return key in obj


def has_method(obj: Any, method: str) -> bool:
    """是否有方法"""
    return hasattr(obj, method) and callable(getattr(obj, method))


def validate(obj: Any, schema: dict) -> tuple:
    """
    简单验证
    
    Args:
        obj: 对象
        schema: {属性: 类型或函数}
        
    Returns:
        (is_valid, errors)
    """
    errors = []
    
    for prop, check in schema.items():
        value = obj.get(prop) if isinstance(obj, dict) else getattr(obj, prop, None)
        
        if callable(check):
            if not check(value):
                errors.append(f"{prop} validation failed")
        elif not isinstance(value, check):
            errors.append(f"{prop} expected {check.__name__}")
    
    return len(errors) == 0, errors


def required(*props: str) -> Callable:
    """生成必填检查函数"""
    def checker(obj: dict) -> bool:
        return all(p in obj for p in props)
    return checker


def optional(type_or_check) -> Callable:
    """生成可选检查函数"""
    def checker(value: Any) -> bool:
        if value is None:
            return True
        if callable(type_or_check):
            return type_or_check(value)
        return isinstance(value, type_or_check)
    return checker


# 导出
__all__ = [
    "is_type",
    "is_nonnull",
    "is_truly",
    "is_falsy",
    "has_property",
    "has_key",
    "has_method",
    "validate",
    "required",
    "optional",
]
