"""
Flags - 功能开关
基于 Claude Code flags.ts 设计

功能开关工具。
"""
from typing import Any, Callable, Dict, Optional


class Flags:
    """
    功能开关
    
    控制功能启用/禁用。
    """
    
    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._values: Dict[str, Any] = {}
        self._overrides: Dict[str, bool] = {}
    
    def enable(self, name: str, value: Any = True) -> None:
        """
        启用开关
        
        Args:
            name: 开关名
            value: 关联值
        """
        self._flags[name] = True
        if value is not True:
            self._values[name] = value
    
    def disable(self, name: str) -> None:
        """禁用开关"""
        self._flags[name] = False
    
    def is_enabled(self, name: str) -> bool:
        """
        检查是否启用
        
        Args:
            name: 开关名
            
        Returns:
            是否启用
        """
        # 检查override
        if name in self._overrides:
            return self._overrides[name]
        
        return self._flags.get(name, False)
    
    def get(self, name: str, default: Any = None) -> Any:
        """
        获取开关值
        
        Args:
            name: 开关名
            default: 默认值
            
        Returns:
            开关值或默认值
        """
        if name in self._values:
            return self._values[name]
        if name in self._flags:
            return self._flags[name]
        return default
    
    def toggle(self, name: str) -> bool:
        """
        切换开关
        
        Args:
            name: 开关名
            
        Returns:
            切换后的状态
        """
        current = self.is_enabled(name)
        if current:
            self.disable(name)
        else:
            self.enable(name)
        return not current
    
    def override(self, name: str, enabled: bool) -> None:
        """
        临时覆盖（优先级最高）
        
        Args:
            name: 开关名
            enabled: 强制状态
        """
        self._overrides[name] = enabled
    
    def clear_override(self, name: str) -> None:
        """清除临时覆盖"""
        if name in self._overrides:
            del self._overrides[name]
    
    def clear_all_overrides(self) -> None:
        """清除所有临时覆盖"""
        self._overrides.clear()
    
    def remove(self, name: str) -> bool:
        """删除开关"""
        if name in self._flags:
            del self._flags[name]
        if name in self._values:
            del self._values[name]
        return True
    
    def list_all(self) -> Dict[str, bool]:
        """列出所有开关"""
        result = dict(self._flags)
        result.update({k: v for k, v in self._overrides.items()})
        return result
    
    def names(self) -> list:
        """获取所有开关名"""
        return list(self._flags.keys())


# 全局实例
_global_flags = Flags()


def flags() -> Flags:
    """获取全局Flags实例"""
    return _global_flags


def enable(name: str, value: Any = True) -> None:
    """全局启用"""
    _global_flags.enable(name, value)


def disable(name: str) -> None:
    """全局禁用"""
    _global_flags.disable(name)


def is_enabled(name: str) -> bool:
    """全局检查"""
    return _global_flags.is_enabled(name)


def get(name: str, default: Any = None) -> Any:
    """全局获取"""
    return _global_flags.get(name, default)


# 导出
__all__ = [
    "Flags",
    "flags",
    "enable",
    "disable",
    "is_enabled",
    "get",
]
