"""
Env - 环境变量
基于 Claude Code env.ts 设计

环境变量工具。
"""
import os
from typing import Any, Dict, Optional


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


def set_(key: str, value: str) -> None:
    """
    设置环境变量
    
    Args:
        key: 变量名
        value: 值
    """
    os.environ[key] = value


def has(key: str) -> bool:
    """检查环境变量是否存在"""
    return key in os.environ


def remove(key: str) -> bool:
    """删除环境变量"""
    if key in os.environ:
        del os.environ[key]
        return True
    return False


def get_int(key: str, default: int = 0) -> int:
    """获取整数"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_float(key: str, default: float = 0.0) -> float:
    """获取浮点数"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_bool(key: str, default: bool = False) -> bool:
    """获取布尔值"""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


def get_list(key: str, separator: str = ',', default: list = None) -> list:
    """获取列表"""
    value = os.environ.get(key)
    if value is None:
        return default or []
    return [v.strip() for v in value.split(separator)]


def all_vars() -> Dict[str, str]:
    """获取所有环境变量"""
    return dict(os.environ)


def clear_cache() -> None:
    """清空缓存（无操作，os.environ直接访问）"""
    pass


# 导出
__all__ = [
    "get",
    "set_",
    "has",
    "remove",
    "get_int",
    "get_float",
    "get_bool",
    "get_list",
    "all_vars",
    "clear_cache",
]
