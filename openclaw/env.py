"""
Env - 环境变量
基于 Claude Code env.ts 设计

环境变量工具。
"""
import os
from typing import Any, Optional


def get(key: str, default: Any = None) -> Any:
    """
    获取环境变量
    
    Args:
        key: 变量名
        default: 默认值
        
    Returns:
        变量值或默认值
    """
    return os.environ.get(key, default)


def set(key: str, value: str) -> None:
    """
    设置环境变量
    
    Args:
        key: 变量名
        value: 变量值
    """
    os.environ[key] = value


def unset(key: str) -> bool:
    """
    删除环境变量
    
    Args:
        key: 变量名
        
    Returns:
        是否成功删除
    """
    if key in os.environ:
        del os.environ[key]
        return True
    return False


def has(key: str) -> bool:
    """
    检查环境变量是否存在
    
    Args:
        key: 变量名
        
    Returns:
        是否存在
    """
    return key in os.environ


def get_int(key: str, default: int = 0) -> int:
    """获取整数环境变量"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_float(key: str, default: float = 0.0) -> float:
    """获取浮点数环境变量"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_bool(key: str, default: bool = False) -> bool:
    """获取布尔环境变量"""
    value = os.environ.get(key, '').lower()
    if value in ('true', '1', 'yes', 'on'):
        return True
    if value in ('false', '0', 'no', 'off'):
        return False
    return default


def get_list(key: str, separator: str = ',', default: list = None) -> list:
    """获取列表环境变量"""
    value = os.environ.get(key)
    if value is None:
        return default or []
    return [v.strip() for v in value.split(separator) if v.strip()]


class Env:
    """
    环境变量类
    
    链式调用。
    """
    
    def __init__(self, prefix: str = ''):
        """
        Args:
            prefix: 变量名前缀
        """
        self._prefix = prefix
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取"""
        return get(f"{self._prefix}{key}", default)
    
    def required(self, key: str) -> str:
        """
        获取必需的环境变量
        
        Raises:
            KeyError: 变量不存在
        """
        full_key = f"{self._prefix}{key}"
        value = os.environ.get(full_key)
        if value is None:
            raise KeyError(f"Required environment variable not set: {full_key}")
        return value
    
    def __getattr__(self, key: str) -> str:
        """属性访问"""
        return self.get(key)


# 带前缀的环境变量
_env = Env()


def with_prefix(prefix: str) -> Env:
    """
    创建带前缀的环境变量访问器
    
    Args:
        prefix: 前缀
        
    Returns:
        Env实例
    """
    return Env(prefix)


# 导出
__all__ = [
    "get",
    "set",
    "unset",
    "has",
    "get_int",
    "get_float",
    "get_bool",
    "get_list",
    "Env",
    "with_prefix",
]
