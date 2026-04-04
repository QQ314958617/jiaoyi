"""
Scope - 作用域
基于 Claude Code scope.ts 设计

作用域工具。
"""
from typing import Any, Callable, Dict, Optional


class Scope:
    """
    作用域链
    
    支持嵌套作用域查找。
    """
    
    def __init__(self, parent: "Scope" = None):
        """
        Args:
            parent: 父作用域
        """
        self._parent = parent
        self._bindings: Dict[str, Any] = {}
    
    def get(self, name: str, default: Any = None) -> Any:
        """
        获取变量
        
        Args:
            name: 变量名
            default: 默认值
            
        Returns:
            变量值
        """
        if name in self._bindings:
            return self._bindings[name]
        if self._parent:
            return self._parent.get(name, default)
        return default
    
    def set(self, name: str, value: Any) -> None:
        """
        设置变量
        
        Args:
            name: 变量名
            value: 值
        """
        self._bindings[name] = value
    
    def has(self, name: str) -> bool:
        """检查变量是否存在"""
        if name in self._bindings:
            return True
        if self._parent:
            return self._parent.has(name)
        return False
    
    def define(self, name: str, value: Any) -> None:
        """在当前作用域定义变量"""
        self._bindings[name] = value
    
    def lookup(self, name: str) -> Optional[Any]:
        """
        查找变量
        
        Args:
            name: 变量名
            
        Returns:
            变量值或None
        """
        if name in self._bindings:
            return self._bindings[name]
        if self._parent:
            return self._parent.lookup(name)
        return None
    
    def child(self) -> "Scope":
        """创建子作用域"""
        return Scope(self)
    
    def clear(self) -> None:
        """清空当前作用域"""
        self._bindings.clear()
    
    def keys(self) -> list:
        """所有变量名"""
        result = list(self._bindings.keys())
        if self._parent:
            result.extend(self._parent.keys())
        return result


class GlobalScope(Scope):
    """全局作用域"""
    
    def __init__(self):
        super().__init__(None)


class LocalScope(Scope):
    """局部作用域"""
    
    def __init__(self, parent: Scope):
        super().__init__(parent)


# 导出
__all__ = [
    "Scope",
    "GlobalScope",
    "LocalScope",
]
