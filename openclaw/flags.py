"""
Flags - 功能开关
基于 Claude Code flags.ts 设计

功能开关管理。
"""
from typing import Callable, Dict, Optional, Any


class FeatureFlags:
    """
    功能开关管理器
    """
    
    def __init__(self):
        self._flags: Dict[str, bool] = {}
        self._overrides: Dict[str, bool] = {}
        self._listeners: Dict[str, list] = {}
    
    def set(self, name: str, value: bool) -> None:
        """
        设置开关值
        
        Args:
            name: 开关名
            value: 值
        """
        old_value = self._flags.get(name)
        self._flags[name] = value
        
        # 通知监听器
        if name in self._listeners and old_value != value:
            for listener in self._listeners[name]:
                try:
                    listener(value)
                except Exception:
                    pass
    
    def get(self, name: str, default: bool = False) -> bool:
        """
        获取开关值
        
        Args:
            name: 开关名
            default: 默认值
            
        Returns:
            开关值
        """
        if name in self._overrides:
            return self._overrides[name]
        return self._flags.get(name, default)
    
    def is_enabled(self, name: str) -> bool:
        """检查开关是否启用"""
        return self.get(name)
    
    def is_disabled(self, name: str) -> bool:
        """检查开关是否禁用"""
        return not self.get(name)
    
    def enable(self, name: str) -> None:
        """启用开关"""
        self.set(name, True)
    
    def disable(self, name: str) -> None:
        """禁用开关"""
        self.set(name, False)
    
    def override(self, name: str, value: bool) -> None:
        """
        覆盖开关值（优先级最高）
        
        Args:
            name: 开关名
            value: 覆盖值
        """
        self._overrides[name] = value
    
    def clear_override(self, name: str) -> None:
        """清除覆盖"""
        if name in self._overrides:
            del self._overrides[name]
    
    def on_change(self, name: str, listener: Callable[[bool], None]) -> Callable:
        """
        监听开关变化
        
        Args:
            name: 开关名
            listener: 监听函数
            
        Returns:
            取消监听函数
        """
        if name not in self._listeners:
            self._listeners[name] = []
        self._listeners[name].append(listener)
        
        def unsubscribe():
            if name in self._listeners:
                self._listeners[name].remove(listener)
        
        return unsubscribe


# 全局实例
_global_flags = FeatureFlags()


def get_feature_flags() -> FeatureFlags:
    """获取全局功能开关管理器"""
    return _global_flags


def is_feature_enabled(name: str) -> bool:
    """检查功能是否启用"""
    return _global_flags.is_enabled(name)


def enable_feature(name: str) -> None:
    """启用功能"""
    _global_flags.enable(name)


def disable_feature(name: str) -> None:
    """禁用功能"""
    _global_flags.disable(name)


# 导出
__all__ = [
    "FeatureFlags",
    "get_feature_flags",
    "is_feature_enabled",
    "enable_feature",
    "disable_feature",
]
