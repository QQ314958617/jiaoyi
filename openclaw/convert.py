"""
Convert - 转换
基于 Claude Code convert.ts 设计

类型转换工具。
"""
from typing import Any, Callable, Dict, TypeVar

T = TypeVar('T')


def to_string(value: Any) -> str:
    """转为字符串"""
    return str(value)


def to_int(value: Any, default: int = 0) -> int:
    """转为整数"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    """转为浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def to_bool(value: Any) -> bool:
    """转为布尔值"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes')
    return bool(value)


def to_list(value: Any) -> list:
    """转为列表"""
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def to_dict(value: Any) -> dict:
    """转为字典"""
    if isinstance(value, dict):
        return value
    if hasattr(value, '__dict__'):
        return vars(value)
    return {}


def to_tuple(value: Any) -> tuple:
    """转为元组"""
    if isinstance(value, tuple):
        return value
    if isinstance(value, (list, set)):
        return tuple(value)
    return (value,)


def to_set(value: Any) -> set:
    """转为集合"""
    if isinstance(value, set):
        return value
    if isinstance(value, (list, tuple)):
        return set(value)
    return {value}


def convert(value: Any, type_name: str, default: Any = None) -> Any:
    """
    转换为指定类型
    
    Args:
        value: 值
        type_name: 类型名 ('str', 'int', 'float', 'bool', 'list', 'dict')
        default: 默认值
        
    Returns:
        转换后的值
    """
    converters = {
        'str': to_string,
        'string': to_string,
        'int': lambda v: to_int(v, default=0),
        'integer': lambda v: to_int(v, default=0),
        'float': lambda v: to_float(v, default=0.0),
        'bool': to_bool,
        'boolean': to_bool,
        'list': to_list,
        'dict': to_dict,
        'tuple': to_tuple,
        'set': to_set,
    }
    
    converter = converters.get(type_name.lower())
    if converter:
        try:
            return converter(value)
        except Exception:
            return default
    
    return default


def try_convert(value: Any, converter: Callable, default: Any = None) -> Any:
    """
    尝试转换
    
    Args:
        value: 值
        converter: 转换函数
        default: 默认值
        
    Returns:
        转换后的值或默认值
    """
    try:
        return converter(value)
    except Exception:
        return default


class TypeConverter:
    """
    类型转换器
    """
    
    def __init__(self):
        self._converters: Dict[str, Callable] = {}
    
    def register(self, type_name: str, converter: Callable) -> None:
        """注册转换器"""
        self._converters[type_name] = converter
    
    def convert(self, value: Any, type_name: str, default: Any = None) -> Any:
        """转换"""
        converter = self._converters.get(type_name.lower())
        if converter:
            return try_convert(value, converter, default)
        return default


def safe_cast(value: Any, target_type: type, default: Any = None) -> Any:
    """
    安全类型转换
    
    Args:
        value: 值
        target_type: 目标类型
        default: 默认值
        
    Returns:
        转换后的值
    """
    try:
        return target_type(value)
    except (ValueError, TypeError):
        return default


# 导出
__all__ = [
    "to_string",
    "to_int",
    "to_float",
    "to_bool",
    "to_list",
    "to_dict",
    "to_tuple",
    "to_set",
    "convert",
    "try_convert",
    "TypeConverter",
    "safe_cast",
]
