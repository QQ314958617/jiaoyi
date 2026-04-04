"""
Env - 环境变量
基于 Claude Code env.ts 设计

环境变量工具。
"""
import os


def get(key: str, default: str = None) -> str:
    """
    获取环境变量
    
    Args:
        key: 变量名
        default: 默认值
        
    Returns:
        值或默认值
    """
    return os.environ.get(key, default)


def set_(key: str, value: str) -> None:
    """
    设置环境变量
    """
    os.environ[key] = value


def unset(key: str) -> None:
    """
    删除环境变量
    """
    os.environ.pop(key, None)


def has(key: str) -> bool:
    """是否存在"""
    return key in os.environ


def list_all() -> dict:
    """列出所有环境变量"""
    return dict(os.environ)


def get_int(key: str, default: int = None) -> int:
    """获取整数"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_bool(key: str, default: bool = None) -> bool:
    """获取布尔值"""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


class Env:
    """环境变量访问器"""
    
    def __getattr__(self, key: str) -> str:
        return get(key)
    
    def __setattr__(self, key: str, value: str) -> None:
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            set_(key, value)
    
    def __has__(self, key: str) -> bool:
        return has(key)


# 导出
__all__ = [
    "get",
    "set_",
    "unset",
    "has",
    "list_all",
    "get_int",
    "get_bool",
    "Env",
]
