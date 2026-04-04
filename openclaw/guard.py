"""
Guard - 守卫
基于 Claude Code guard.ts 设计

守卫和守卫链工具。
"""
from typing import Any, Callable, List


class Guard:
    """
    守卫
    
    验证和转换值。
    """
    
    def __init__(self, value: Any):
        self._value = value
        self._errors: List[str] = []
    
    def validate(self, fn: Callable[[Any], bool], message: str) -> "Guard":
        """添加验证"""
        if not fn(self._value):
            self._errors.append(message)
        return self
    
    def required(self, message: str = "Value is required") -> "Guard":
        """必需"""
        if self._value is None or self._value == '':
            self._errors.append(message)
        return self
    
    def type_is(self, expected_type: type, message: str = None) -> "Guard":
        """类型检查"""
        if message is None:
            message = f"Expected {expected_type.__name__}"
        if not isinstance(self._value, expected_type):
            self._errors.append(message)
        return self
    
    def min_length(self, length: int, message: str = None) -> "Guard":
        """最小长度"""
        if message is None:
            message = f"Min length is {length}"
        if hasattr(self._value, '__len__') and len(self._value) < length:
            self._errors.append(message)
        return self
    
    def max_length(self, length: int, message: str = None) -> "Guard":
        """最大长度"""
        if message is None:
            message = f"Max length is {length}"
        if hasattr(self._value, '__len__') and len(self._value) > length:
            self._errors.append(message)
        return self
    
    def pattern(self, regex: str, message: str = None) -> "Guard":
        """正则匹配"""
        import re
        if message is None:
            message = f"Does not match pattern: {regex}"
        if not re.match(regex, str(self._value)):
            self._errors.append(message)
        return self
    
    def in_range(self, min_val: float, max_val: float, message: str = None) -> "Guard":
        """范围检查"""
        if message is None:
            message = f"Must be between {min_val} and {max_val}"
        if isinstance(self._value, (int, float)):
            if self._value < min_val or self._value > max_val:
                self._errors.append(message)
        return self
    
    def is_valid(self) -> bool:
        """是否有效"""
        return len(self._errors) == 0
    
    def errors(self) -> List[str]:
        """获取错误列表"""
        return self._errors.copy()
    
    def get(self) -> Any:
        """获取值（如果有错误则抛异常）"""
        if self._errors:
            raise ValueError(f"Validation failed: {', '.join(self._errors)}")
        return self._value


def guard(value: Any) -> Guard:
    """
    创建守卫
    
    Args:
        value: 要验证的值
        
    Returns:
        Guard实例
    """
    return Guard(value)


class GuardChain:
    """
    守卫链
    
    链式验证。
    """
    
    def __init__(self, value: Any):
        self._guard = Guard(value)
    
    def required(self) -> "GuardChain":
        self._guard.required()
        return self
    
    def type_is(self, t: type) -> "GuardChain":
        self._guard.type_is(t)
        return self
    
    def min_length(self, length: int) -> "GuardChain":
        self._guard.min_length(length)
        return self
    
    def max_length(self, length: int) -> "GuardChain":
        self._guard.max_length(length)
        return self
    
    def pattern(self, regex: str) -> "GuardChain":
        self._guard.pattern(regex)
        return self
    
    def in_range(self, min_val: float, max_val: float) -> "GuardChain":
        self._guard.in_range(min_val, max_val)
        return self
    
    def get(self) -> Any:
        return self._guard.get()
    
    def is_valid(self) -> bool:
        return self._guard.is_valid()
    
    def errors(self) -> List[str]:
        return self._guard.errors()


# 导出
__all__ = [
    "Guard",
    "guard",
    "GuardChain",
]
