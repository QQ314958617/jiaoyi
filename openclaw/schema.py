"""
Schema - 模式
基于 Claude Code schema.ts 设计

数据模式验证工具。
"""
from typing import Any, Callable, Dict, List, Optional, Union


class Schema:
    """
    数据模式
    
    定义和验证数据结构。
    """
    
    def __init__(self, schema: Dict[str, Any]):
        """
        Args:
            schema: 模式定义
        """
        self._schema = schema
        self._validators: Dict[str, List[Callable]] = {}
    
    def field(self, name: str, *validators: Callable) -> "Schema":
        """
        为字段添加验证器
        
        Args:
            name: 字段名
            *validators: 验证函数 (value) -> bool 或 (value) -> error_message
        """
        if name not in self._validators:
            self._validators[name] = []
        self._validators[name].extend(validators)
        return self
    
    def validate(self, data: dict) -> tuple:
        """
        验证数据
        
        Args:
            data: 要验证的数据
            
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        for field_name, field_schema in self._schema.items():
            value = data.get(field_name)
            
            # 类型检查
            expected_type = field_schema.get('type')
            if expected_type and value is not None:
                if not isinstance(value, expected_type):
                    errors.append(f"{field_name}: expected {expected_type.__name__}, got {type(value).__name__}")
            
            # 必填检查
            if field_schema.get('required', False) and value is None:
                errors.append(f"{field_name}: required")
            
            # 自定义验证器
            for validator in self._validators.get(field_name, []):
                try:
                    result = validator(value)
                    if result is False:
                        errors.append(f"{field_name}: validation failed")
                    elif isinstance(result, str):
                        errors.append(f"{field_name}: {result}")
                except Exception as e:
                    errors.append(f"{field_name}: {str(e)}")
        
        return len(errors) == 0, errors
    
    def is_valid(self, data: dict) -> bool:
        """检查数据是否有效"""
        valid, _ = self.validate(data)
        return valid


def string() -> type:
    """字符串类型"""
    return str


def number() -> type:
    """数字类型"""
    return (int, float)


def boolean() -> type:
    """布尔类型"""
    return bool


def array() -> type:
    """数组类型"""
    return list


def object() -> type:
    """对象类型"""
    return dict


def required(schema: "Schema", field: str) -> "Schema":
    """标记字段为必填"""
    if field not in schema._schema:
        schema._schema[field] = {}
    schema._schema[field]['required'] = True
    return schema


def typed(expected_type: type) -> Callable:
    """类型验证器"""
    def validator(value) -> bool:
        return isinstance(value, expected_type)
    return validator


def min_length(min_len: int) -> Callable:
    """最小长度验证"""
    def validator(value) -> bool:
        if value is None:
            return True
        return len(value) >= min_len
    return validator


def max_length(max_len: int) -> Callable:
    """最大长度验证"""
    def validator(value) -> bool:
        if value is None:
            return True
        return len(value) <= max_len
    return validator


def pattern(regex: str) -> Callable:
    """正则验证"""
    import re
    compiled = re.compile(regex)
    
    def validator(value) -> bool:
        if value is None:
            return True
        return bool(compiled.match(str(value)))
    return validator


def in_values(*values) -> Callable:
    """枚举验证"""
    def validator(value) -> bool:
        return value in values
    return validator


# 导出
__all__ = [
    "Schema",
    "string",
    "number",
    "boolean",
    "array",
    "object",
    "required",
    "typed",
    "min_length",
    "max_length",
    "pattern",
    "in_values",
]
