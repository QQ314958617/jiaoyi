"""
Validate - 数据验证
基于 Claude Code validate.ts 设计

数据验证工具。
"""
import re
from typing import Any, Callable, List, Optional


class ValidationError(Exception):
    """验证错误"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class Validator:
    """
    数据验证器
    
    链式调用验证规则。
    """
    
    def __init__(self, value: Any, field_name: str = None):
        self._value = value
        self._field_name = field_name
        self._errors: List[str] = []
    
    def validate(self) -> Any:
        """
        执行验证
        
        Returns:
            验证通过的值
            
        Raises:
            ValidationError: 验证失败
        """
        if self._errors:
            error_msg = self._errors[0]
            if self._field_name:
                error_msg = f"{self._field_name}: {error_msg}"
            raise ValidationError(error_msg, self._field_name)
        
        return self._value
    
    def is_valid(self) -> bool:
        """检查是否有效"""
        return len(self._errors) == 0
    
    def required(self, message: str = "Field is required") -> "Validator":
        """必填验证"""
        if self._value is None or self._value == "":
            self._errors.append(message)
        return self
    
    def min_length(self, length: int, message: str = None) -> "Validator":
        """最小长度验证"""
        if self._value is not None and len(str(self._value)) < length:
            self._errors.append(message or f"Minimum length is {length}")
        return self
    
    def max_length(self, length: int, message: str = None) -> "Validator":
        """最大长度验证"""
        if self._value is not None and len(str(self._value)) > length:
            self._errors.append(message or f"Maximum length is {length}")
        return self
    
    def pattern(self, regex: str, message: str = "Invalid format") -> "Validator":
        """正则验证"""
        if self._value is not None:
            if not re.match(regex, str(self._value)):
                self._errors.append(message)
        return self
    
    def email(self, message: str = "Invalid email format") -> "Validator":
        """邮箱验证"""
        return self.pattern(r'^[\w\.-]+@[\w\.-]+\.\w+$', message)
    
    def url(self, message: str = "Invalid URL format") -> "Validator":
        """URL验证"""
        return self.pattern(r'^https?://[\w\.-]+(?:/[\w\.-]*)*/?$', message)
    
    def min_value(self, min_val: int, message: str = None) -> "Validator":
        """最小值验证"""
        if self._value is not None and self._value < min_val:
            self._errors.append(message or f"Minimum value is {min_val}")
        return self
    
    def max_value(self, max_val: int, message: str = None) -> "Validator":
        """最大值验证"""
        if self._value is not None and self._value > max_val:
            self._errors.append(message or f"Maximum value is {max_val}")
        return self
    
    def one_of(self, values: list, message: str = None) -> "Validator":
        """枚举验证"""
        if self._value is not None and self._value not in values:
            self._errors.append(
                message or f"Must be one of: {', '.join(str(v) for v in values)}"
            )
        return self
    
    def custom(self, fn: Callable[[Any], bool], message: str) -> "Validator":
        """自定义验证"""
        if self._value is not None and not fn(self._value):
            self._errors.append(message)
        return self


def validate(value: Any, *rules: Callable[[Validator], Validator]) -> Any:
    """
    验证值
    
    Args:
        value: 要验证的值
        *rules: 验证规则函数
        
    Returns:
        验证通过的值
        
    Raises:
        ValidationError: 验证失败
    """
    validator = Validator(value)
    for rule in rules:
        rule(validator)
    return validator.validate()


def validate_field(
    value: Any,
    field_name: str,
    *rules: Callable[[Validator], Validator],
) -> Any:
    """
    验证字段
    
    Args:
        value: 要验证的值
        field_name: 字段名
        *rules: 验证规则函数
        
    Returns:
        验证通过的值
        
    Raises:
        ValidationError: 验证失败
    """
    validator = Validator(value, field_name)
    for rule in rules:
        rule(validator)
    return validator.validate()


def is_valid(value: Any, *rules: Callable[[Validator], Validator]) -> bool:
    """
    检查值是否有效
    
    Args:
        value: 要检查的值
        *rules: 验证规则函数
        
    Returns:
        是否有效
    """
    validator = Validator(value)
    for rule in rules:
        rule(validator)
    return validator.is_valid()


# 便捷规则函数
def required(message: str = None):
    """必填规则"""
    def rule(v: Validator):
        v.required(message)
    return rule


def min_length(length: int, message: str = None):
    """最小长度规则"""
    def rule(v: Validator):
        v.min_length(length, message)
    return rule


def email(message: str = None):
    """邮箱规则"""
    def rule(v: Validator):
        v.email(message)
    return rule


# 导出
__all__ = [
    "ValidationError",
    "Validator",
    "validate",
    "validate_field",
    "is_valid",
    "required",
    "min_length",
    "email",
]
