"""
Config - 配置
基于 Claude Code config.ts 设计

配置管理工具。
"""
from typing import Any, Callable, Dict, List, Optional


class Config:
    """
    配置管理
    
    支持嵌套、默认值和变更通知。
    """
    
    def __init__(self, initial: Dict[str, Any] = None):
        """
        Args:
            initial: 初始配置
        """
        self._data: Dict[str, Any] = initial or {}
        self._defaults: Dict[str, Any] = {}
        self._listeners: Dict[str, List[Callable]] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置
        
        Args:
            key: 键（支持点分隔，如 'db.host'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return self._defaults.get(key, default)
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置
        
        Args:
            key: 键
            value: 值
        """
        old_value = self.get(key)
        
        keys = key.split('.')
        current = self._data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        
        # 通知监听器
        self._notify(key, old_value, value)
    
    def has(self, key: str) -> bool:
        """检查配置是否存在"""
        keys = key.split('.')
        value = self._data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False
        
        return True
    
    def delete(self, key: str) -> bool:
        """删除配置"""
        keys = key.split('.')
        current = self._data
        
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                return False
            current = current[k]
        
        if keys[-1] in current:
            del current[keys[-1]]
            return True
        return False
    
    def set_default(self, key: str, value: Any) -> None:
        """设置默认值"""
        self._defaults[key] = value
    
    def on_change(self, key: str, listener: Callable) -> Callable:
        """
        监听配置变更
        
        Args:
            key: 键（支持通配符如 '*'）
            listener: (old_value, new_value) -> None
            
        Returns:
            取消订阅函数
        """
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(listener)
        
        return lambda: self._listeners[key].remove(listener)
    
    def _notify(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知监听器"""
        # 精确匹配
        for listener in self._listeners.get(key, []):
            try:
                listener(old_value, new_value)
            except Exception:
                pass
        
        # 通配符匹配
        for pattern, listeners in self._listeners.items():
            if pattern != key and self._match(key, pattern):
                for listener in listeners:
                    try:
                        listener(old_value, new_value)
                    except Exception:
                        pass
    
    def _match(self, key: str, pattern: str) -> bool:
        """通配符匹配"""
        if pattern == '*':
            return True
        if pattern.endswith('.*'):
            prefix = pattern[:-2]
            return key.startswith(prefix)
        return key == pattern
    
    def merge(self, other: dict) -> None:
        """合并配置"""
        self._data = self._deep_merge(self._data, other)
    
    def _deep_merge(self, base: dict, update: dict) -> dict:
        """深度合并"""
        result = dict(base)
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def to_dict(self) -> dict:
        """导出为字典"""
        return dict(self._data)
    
    def clear(self) -> None:
        """清空配置"""
        self._data.clear()


def create_config(initial: Dict[str, Any] = None) -> Config:
    """
    创建配置
    
    Args:
        initial: 初始配置
        
    Returns:
        Config实例
    """
    return Config(initial)


# 导出
__all__ = [
    "Config",
    "create_config",
]
