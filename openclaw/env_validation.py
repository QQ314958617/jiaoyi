"""
EnvValidation - 环境变量验证
基于 Claude Code env_validation.ts 设计

环境变量验证工具。
"""
import os
from typing import Dict, Any, Callable, List, Optional


class EnvValidation:
    """
    环境变量验证器
    """
    
    def __init__(self):
        self._rules: Dict[str, List[Callable]] = {}
        self._errors: List[str] = []
    
    def add_rule(self, key: str, validator: Callable[[str], bool], 
                 message: str = None):
        """
        添加验证规则
        
        Args:
            key: 环境变量名
            validator: 验证函数
            message: 错误消息
        """
        if key not in self._rules:
            self._rules[key] = []
        self._rules[key].append((validator, message))
    
    def require(self, key: str):
        """必须存在"""
        self.add_rule(
            key,
            lambda v: v is not None and v != "",
            f"{key} is required"
        )
    
    def require_one_of(self, keys: List[str]):
        """至少一个必须存在"""
        def validator(values: List[str]) -> bool:
            return any(v for v in values if v)
        
        self.add_rule(
            ",".join(keys),
            lambda _: any(os.environ.get(k) for k in keys),
            f"One of {keys} is required"
        )
    
    def validate(self) -> bool:
        """
        验证所有规则
        
        Returns:
            是否通过
        """
        self._errors = []
        
        for key, rules in self._rules.items():
            values = key.split(",")
            value = os.environ.get(key.split(",")[0]) if len(values) == 1 else [os.environ.get(v) for v in values]
            
            for validator, message in rules:
                try:
                    if len(values) == 1:
                        if not validator(value):
                            self._errors.append(message or f"{key} validation failed")
                    else:
                        if not validator(value):
                            self._errors.append(message or f"{key} validation failed")
                except Exception as e:
                    self._errors.append(str(e))
        
        return len(self._errors) == 0
    
    def errors(self) -> List[str]:
        """获取错误列表"""
        return self._errors


def require(key: str) -> bool:
    """检查环境变量是否存在"""
    return os.environ.get(key) is not None


def get(key: str, default: str = None) -> str:
    """获取环境变量"""
    return os.environ.get(key, default)


def get_int(key: str, default: int = None) -> Optional[int]:
    """获取整数"""
    value = os.environ.get(key)
    if value:
        try:
            return int(value)
        except ValueError:
            return default
    return default


def get_bool(key: str, default: bool = False) -> bool:
    """获取布尔值"""
    value = os.environ.get(key)
    if value:
        return value.lower() in ('true', '1', 'yes', 'on')
    return default


def require_keys(*keys: str):
    """
    要求多个环境变量都存在
    
    Raises:
        EnvironmentError: 如果任何key不存在
    """
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {missing}")


# 导出
__all__ = [
    "EnvValidation",
    "require",
    "get",
    "get_int",
    "get_bool",
    "require_keys",
]
