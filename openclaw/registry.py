"""
Registry - 注册表
基于 Claude Code registry.ts 设计

注册表工具。
"""
from typing import Any, Callable, Dict, List, Optional


class Registry:
    """
    注册表
    
    管理命名条目。
    """
    
    def __init__(self):
        self._entries: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
    
    def register(self, name: str, entry: Any) -> None:
        """
        注册条目
        
        Args:
            name: 条目名
            entry: 条目
        """
        self._entries[name] = entry
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """
        注册工厂函数
        
        Args:
            name: 条目名
            factory: 工厂函数 () -> entry
        """
        self._factories[name] = factory
    
    def get(self, name: str, default: Any = None) -> Any:
        """
        获取条目
        
        Args:
            name: 条目名
            default: 默认值
            
        Returns:
            条目或默认值
        """
        if name in self._entries:
            return self._entries[name]
        
        if name in self._factories:
            entry = self._factories[name]()
            self._entries[name] = entry
            return entry
        
        return default
    
    def has(self, name: str) -> bool:
        """检查是否存在"""
        return name in self._entries or name in self._factories
    
    def unregister(self, name: str) -> bool:
        """取消注册"""
        if name in self._entries:
            del self._entries[name]
            return True
        if name in self._factories:
            del self._factories[name]
            return True
        return False
    
    def list_entries(self) -> List[str]:
        """列出所有条目名"""
        return list(self._entries.keys())
    
    def clear(self) -> None:
        """清空"""
        self._entries.clear()
        self._factories.clear()


class SingletonRegistry(Registry):
    """
    单例注册表
    
    自动创建单例。
    """
    
    def get(self, name: str, default: Any = None) -> Any:
        """获取单例"""
        if name not in self._entries:
            if name in self._factories:
                self._entries[name] = self._factories[name]()
            elif default is not None:
                self._entries[name] = default
            else:
                return default
        
        return self._entries[name]
    
    def get_or_create(self, name: str, factory: Callable) -> Any:
        """
        获取或创建单例
        
        Args:
            name: 条目名
            factory: 工厂函数
            
        Returns:
            单例
        """
        if name not in self._entries:
            self._entries[name] = factory()
        return self._entries[name]


class PluginRegistry(Registry):
    """
    插件注册表
    
    支持插件启用/禁用。
    """
    
    def __init__(self):
        super().__init__()
        self._enabled: Dict[str, bool] = {}
    
    def register(self, name: str, plugin: Any) -> None:
        """注册插件"""
        super().register(name, plugin)
        self._enabled[name] = True
    
    def enable(self, name: str) -> bool:
        """启用插件"""
        if name in self._entries:
            self._enabled[name] = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用插件"""
        if name in self._entries:
            self._enabled[name] = False
            return True
        return False
    
    def is_enabled(self, name: str) -> bool:
        """是否启用"""
        return self._enabled.get(name, False)
    
    def get_enabled(self) -> List[Any]:
        """获取所有已启用的插件"""
        return [self._entries[name] for name in self._entries if self._enabled.get(name)]


# 全局注册表
_global_registry = Registry()


def global_registry() -> Registry:
    """获取全局注册表"""
    return _global_registry


def register(name: str, entry: Any) -> None:
    """全局注册"""
    _global_registry.register(name, entry)


def get_registered(name: str, default: Any = None) -> Any:
    """获取全局注册"""
    return _global_registry.get(name, default)


# 导出
__all__ = [
    "Registry",
    "SingletonRegistry",
    "PluginRegistry",
    "global_registry",
    "register",
    "get_registered",
]
