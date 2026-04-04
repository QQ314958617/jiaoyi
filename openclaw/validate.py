"""
Validate - 验证
基于 Claude Code validate.ts 设计

验证工具。
"""
from typing import Any, Callable


def required(value: Any) -> bool:
    """非空验证"""
    if value is None:
        return False
    if isinstance(value, (str, list, dict, tuple, set)):
        return len(value) > 0
    return True


def min_length(length: int) -> Callable:
    """最小长度"""
    def validator(value: Any) -> bool:
        if value is None:
            return True
        return len(value) >= length
    return validator


def max_length(length: int) -> Callable:
    """最大长度"""
    def validator(value: Any) -> bool:
        if value is None:
            return True
        return len(value) <= length
    return validator


def pattern(regex: str) -> Callable:
    """正则验证"""
    import re
    compiled = re.compile(regex)
    
    def validator(value: str) -> bool:
        if value is None:
            return True
        return bool(compiled.match(str(value)))
    return validator


def email(value: str) -> bool:
    """邮箱验证"""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, str(value))) if value else False


def url(value: str) -> bool:
    """URL验证"""
    import re
    pattern = r'^https?://[\w\.-]+\.\w+'
    return bool(re.match(pattern, str(value))) if value else False


def min_value(min_val: Any) -> Callable:
    """最小值"""
    def validator(value: Any) -> bool:
        if value is None:
            return True
        return value >= min_val
    return validator


def max_value(max_val: Any) -> Callable:
    """最大值"""
    def validator(value: Any) -> bool:
        if value is None:
            return True
        return value <= max_val
    return validator


def in_range(min_val: Any, max_val: Any) -> Callable:
    """范围验证"""
    def validator(value: Any) -> bool:
        if value is None:
            return True
        return min_val <= value <= max_val
    return validator


def one_of(*choices) -> Callable:
    """枚举验证"""
    def validator(value: Any) -> bool:
        return value in choices
    return validator


class Validator:
    """验证器"""
    
    def __init__(self):
        self._rules = []
    
    def add(self, rule: Callable) -> "Validator":
        """添加规则"""
        self._rules.append(rule)
        return self
    
    def validate(self, value: Any) -> tuple:
        """验证"""
        errors = []
        for rule in self._rules:
            if not rule(value):
                errors.append("Validation failed")
        return len(errors) == 0, errors
    
    def __call__(self, value: Any) -> bool:
        """快速验证"""
        valid, _ = self.validate(value)
        return valid


# 导出
__all__ = [
    "required",
    "min_length",
    "max_length",
    "pattern",
    "email",
    "url",
    "min_value",
    "max_value",
    "in_range",
    "one_of",
    "Validator",
]
