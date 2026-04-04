"""
CWD - 工作目录管理
基于 Claude Code cwd.ts 设计

支持异步上下文中的工作目录覆盖，
使并发agents可以各自看到自己的工作目录。
"""
import os
from contextvars import ContextVar
from typing import Optional

# 上下文变量
_cwd_override: ContextVar[Optional[str]] = ContextVar('cwd_override', default=None)


class CwdManager:
    """
    工作目录管理器
    
    支持：
    - 获取当前工作目录
    - 在异步上下文中覆盖工作目录
    - 获取原始工作目录
    """
    
    _original_cwd: str = ""
    _current_cwd: str = ""
    
    def __init__(self):
        self._original_cwd = os.getcwd()
        self._current_cwd = self._original_cwd
    
    def get(self) -> str:
        """
        获取当前工作目录
        
        Returns:
            覆盖的工作目录或全局工作目录
        """
        override = _cwd_override.get()
        return override if override else self._current_cwd
    
    def set(self, path: str) -> None:
        """
        设置当前工作目录
        
        Args:
            path: 新的工作目录
        """
        self._current_cwd = path
        try:
            os.chdir(path)
        except Exception:
            pass
    
    def get_original(self) -> str:
        """
        获取原始工作目录
        
        Returns:
            原始工作目录
        """
        return self._original_cwd
    
    def run_with_override(self, path: str, fn: callable) -> any:
        """
        在覆盖的工作目录中执行函数
        
        Args:
            path: 覆盖的工作目录
            fn: 要执行的函数
            
        Returns:
            函数返回值
        """
        token = _cwd_override.set(path)
        try:
            original = self._current_cwd
            self._current_cwd = path
            try:
                os.chdir(path)
            except Exception:
                pass
            result = fn()
            self._current_cwd = original
            try:
                os.chdir(original)
            except Exception:
                pass
            return result
        finally:
            _cwd_override.reset(token)


# 全局实例
_cwd_manager: Optional[CwdManager] = None


def get_cwd_manager() -> CwdManager:
    """获取全局CWD管理器"""
    global _cwd_manager
    if _cwd_manager is None:
        _cwd_manager = CwdManager()
    return _cwd_manager


def pwd() -> str:
    """获取当前工作目录"""
    return get_cwd_manager().get()


def get_cwd() -> str:
    """获取当前或原始工作目录"""
    return get_cwd_manager().get()


def run_with_cwd_override(cwd: str, fn: callable) -> any:
    """在覆盖的工作目录中执行函数"""
    return get_cwd_manager().run_with_override(cwd, fn)


# 导出
__all__ = [
    "CwdManager",
    "get_cwd_manager",
    "pwd",
    "get_cwd",
    "run_with_cwd_override",
]
