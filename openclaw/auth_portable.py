"""
AuthPortable - 便携认证
基于 Claude Code auth_portable.ts 设计

便携认证存储工具。
"""
import os
import json
from typing import Optional, Dict


class AuthPortable:
    """
    便携式认证存储
    
    将认证信息存储在文件中。
    """
    
    def __init__(self, path: str = "~/.config/auth_portable.json"):
        """
        Args:
            path: 认证文件路径
        """
        self._path = os.path.expanduser(path)
        self._data: Dict[str, str] = {}
        self._load()
    
    def _load(self):
        """加载认证文件"""
        if os.path.exists(self._path):
            try:
                with open(self._path, 'r') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
    
    def _save(self):
        """保存认证文件"""
        os.makedirs(os.path.dirname(self._path) or '.', exist_ok=True)
        with open(self._path, 'w') as f:
            json.dump(self._data, f, indent=2)
    
    def get(self, key: str) -> Optional[str]:
        """获取认证值"""
        return self._data.get(key)
    
    def set(self, key: str, value: str):
        """设置认证值"""
        self._data[key] = value
        self._save()
    
    def has(self, key: str) -> bool:
        """检查是否存在"""
        return key in self._data
    
    def remove(self, key: str):
        """移除认证"""
        self._data.pop(key, None)
        self._save()
    
    def clear(self):
        """清空所有认证"""
        self._data = {}
        self._save()
    
    def keys(self) -> list:
        """获取所有键"""
        return list(self._data.keys())


# 全局实例
_auth: Optional[AuthPortable] = None


def get_auth(path: str = None) -> AuthPortable:
    """获取全局认证实例"""
    global _auth
    if _auth is None:
        _auth = AuthPortable(path or "~/.config/auth_portable.json")
    return _auth


def get(key: str) -> Optional[str]:
    """获取认证值"""
    return get_auth().get(key)


def set_(key: str, value: str):
    """设置认证值"""
    get_auth().set(key, value)


# 导出
__all__ = [
    "AuthPortable",
    "get_auth",
    "get",
    "set_",
]
