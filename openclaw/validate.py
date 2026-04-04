"""
Validate - 验证器
基于 Claude Code validate.ts 设计

数据验证工具。
"""
import re
from typing import Any, Callable, List, Optional


class ValidationResult:
    """验证结果"""
    
    def __init__(self):
        self._errors: List[str] = []
        self._warnings: List[str] = []
    
    @property
    def is_valid(self) -> bool:
        """是否有效"""
        return len(self._errors) == 0
    
    @property
    def errors(self) -> List[str]:
        """错误列表"""
        return self._errors.copy()
    
    @property
    def warnings(self) -> List[str]:
        """警告列表"""
        return self._warnings.copy()
    
    def add_error(self, message: str) -> "ValidationResult":
        """添加错误"""
        self._errors.append(message)
        return self
    
    def add_warning(self, message: str) -> "ValidationResult":
        """添加警告"""
        self._warnings.append(message)
        return self
    
    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """合并结果"""
        self._errors.extend(other._errors)
        self._warnings.extend(other._warnings)
        return self


class Validator:
    """
    验证器
    
    链式调用验证。
    """
    
    def __init__(self, value: Any):
        self._value = value
        self._result = ValidationResult()
    
    def validate(self) -> ValidationResult:
        """执行验证"""
        return self._result
    
    def required(self, message: str = "Value is required") -> "Validator":
        """必填"""
        if self._value is None or self._value == '':
            self._result.add_error(message)
        return self
    
    def not_empty(self, message: str = "Value cannot be empty") -> "Validator":
        """非空"""
        if self._value is None:
            return self
        if hasattr(self._value, '__len__') and len(self._value) == 0:
            self._result.add_error(message)
        return self
    
    def type_is(self, expected_type: type, message: str = None) -> "Validator":
        """类型检查"""
        if message is None:
            message = f"Expected {expected_type.__name__}, got {type(self._value).__name__}"
        if not isinstance(self._value, expected_type):
            self._result.add_error(message)
        return self
    
    def min_length(self, length: int, message: str = None) -> "Validator":
        """最小长度"""
        if message is None:
            message = f"Length must be at least {length}"
        if self._value is not None and hasattr(self._value, '__len__'):
            if len(self._value) < length:
                self._result.add_error(message)
        return self
    
    def max_length(self, length: int, message: str = None) -> "Validator":
        """最大长度"""
        if message is None:
            message = f"Length must be at most {length}"
        if self._value is not None and hasattr(self._value, '__len__'):
            if len(self._value) > length:
                self._result.add_error(message)
        return self
    
    def min_value(self, min_val: float, message: str = None) -> "Validator":
        """最小值"""
        if message is None:
            message = f"Value must be at least {min_val}"
        if self._value is not None and isinstance(self._value, (int, float)):
            if self._value < min_val:
                self._result.add_error(message)
        return self
    
    def max_value(self, max_val: float, message: str = None) -> "Validator":
        """最大值"""
        if message is None:
            message = f"Value must be at most {max_val}"
        if self._value is not None and isinstance(self._value, (int, float)):
            if self._value > max_val:
                self._result.add_error(message)
        return self
    
    def pattern(self, regex: str, message: str = None) -> "Validator":
        """正则匹配"""
        if message is None:
            message = f"Value does not match pattern: {regex}"
        if self._value is not None and isinstance(self._value, str):
            if not re.match(regex, self._value):
                self._result.add_error(message)
        return self
    
    def email(self, message: str = "Invalid email format") -> "Validator":
        """邮箱格式"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return self.pattern(pattern, message)
    
    def url(self, message: str = "Invalid URL format") -> "Validator":
        """URL格式"""
        pattern = r'https?://[^\s]+'
        return self.pattern(pattern, message)
    
    def one_of(self, options: List[Any], message: str = None) -> "Validator":
        """枚举值"""
        if message is None:
            message = f"Value must be one of: {options}"
        if self._value not in options:
            self._result.add_error(message)
        return self
    
    def custom(self, fn: Callable[[Any], bool], message: str) -> "Validator":
        """自定义验证"""
        try:
            if not fn(self._value):
                self._result.add_error(message)
        except Exception:
            self._result.add_error(message)
        return self


def validate(value: Any) -> Validator:
    """
    创建验证器
    
    Args:
        value: 要验证的值
        
    Returns:
        Validator实例
    """
    return Validator(value)


def is_valid_email(email: str) -> bool:
    """是否为有效邮箱"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """是否为有效URL"""
    pattern = r'https?://[^\s]+'
    return bool(re.match(pattern, url))


def is_valid_phone(phone: str) -> bool:
    """是否为有效电话"""
    pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    return bool(re.match(pattern, phone))


# 导出
__all__ = [
    "ValidationResult",
    "Validator",
    "validate",
    "is_valid_email",
    "is_valid_url",
    "is_valid_phone",
]
