"""
Auth - 认证
基于 Claude Code auth.ts 设计

简单认证工具。
"""
import os
from typing import Optional, Dict


class Auth:
    """
    简单认证管理
    """
    
    def __init__(self):
        self._tokens: Dict[str, str] = {}
    
    def set_token(self, service: str, token: str):
        """设置服务令牌"""
        self._tokens[service] = token
    
    def get_token(self, service: str) -> Optional[str]:
        """获取服务令牌"""
        return self._tokens.get(service)
    
    def has_token(self, service: str) -> bool:
        """是否有令牌"""
        return service in self._tokens
    
    def remove_token(self, service: str):
        """移除令牌"""
        self._tokens.pop(service, None)
    
    def clear(self):
        """清空所有令牌"""
        self._tokens.clear()


# 从环境变量加载令牌
def load_from_env(prefix: str = ""):
    """
    从环境变量加载令牌
    
    环境变量格式: {prefix}GITHUB_TOKEN=xxx
    """
    auth = Auth()
    
    for key, value in os.environ.items():
        if key.endswith("_TOKEN") and value:
            service = key.replace("_TOKEN", "").lower()
            auth.set_token(service, value)
        elif key.startswith(prefix) and "TOKEN" in key and value:
            service = key.replace(f"{prefix}_", "").replace("_TOKEN", "").lower()
            auth.set_token(service, value)
    
    return auth


# GitHub Token
def get_github_token() -> Optional[str]:
    """获取GitHub Token"""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def is_authenticated() -> bool:
    """是否已认证"""
    return get_github_token() is not None


# 导出
__all__ = [
    "Auth",
    "load_from_env",
    "get_github_token",
    "is_authenticated",
]
