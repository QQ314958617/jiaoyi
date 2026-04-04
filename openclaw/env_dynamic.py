"""
EnvDynamic - 动态环境变量
基于 Claude Code env_dynamic.ts 设计

动态环境变量工具。
"""
import os
from typing import Dict, Callable


class DynamicEnv:
    """
    动态环境变量
    """
    
    def __init__(self):
        self._overrides: Dict[str, str] = {}
        self._transforms: Dict[str, Callable] = {}
    
    def set(self, key: str, value: str):
        """设置变量"""
        self._overrides[key] = value
    
    def get(self, key: str) -> str:
        """获取变量"""
        if key in self._overrides:
            return self._overrides[key]
        return os.environ.get(key)
    
    def transform(self, key: str, fn: Callable[[str], str]):
        """
        添加转换函数
        
        获取时自动应用转换
        """
        self._transforms[key] = fn
    
    def resolve(self, key: str) -> str:
        """解析变量（带转换）"""
        value = self.get(key)
        if key in self._transforms and value is not None:
            return self._transforms[key](value)
        return value
    
    def unset(self, key: str):
        """删除变量"""
        self._overrides.pop(key, None)
        self._transforms.pop(key, None)
    
    def clear(self):
        """清空"""
        self._overrides.clear()
        self._transforms.clear()
    
    def to_dict(self) -> Dict[str, str]:
        """导出为字典"""
        result = dict(os.environ)
        result.update(self._overrides)
        return result


# 全局实例
_dynamic_env = DynamicEnv()


def set_(key: str, value: str):
    """设置动态变量"""
    _dynamic_env.set(key, value)


def get(key: str) -> str:
    """获取动态变量"""
    return _dynamic_env.get(key)


def transform(key: str, fn: Callable[[str], str]):
    """添加转换"""
    _dynamic_env.transform(key, fn)


def unset(key: str):
    """删除动态变量"""
    _dynamic_env.unset(key)


def resolve(key: str) -> str:
    """解析动态变量"""
    return _dynamic_env.resolve(key)


# 导出
__all__ = [
    "DynamicEnv",
    "set_",
    "get",
    "transform",
    "unset",
    "resolve",
]
