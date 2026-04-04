"""
Prop - 属性
基于 Claude Code prop.ts 设计

属性工具。
"""
from typing import Any, Callable, Dict, Generic, TypeVar

T = TypeVar('T')


class Prop(Generic[T]):
    """
    可观察属性
    
    值变化时通知订阅者。
    """
    
    def __init__(self, initial_value: T):
        """
        Args:
            initial_value: 初始值
        """
        self._value = initial_value
        self._listeners: list = []
    
    @property
    def value(self) -> T:
        """获取值"""
        return self._value
    
    @value.setter
    def value(self, new_value: T) -> None:
        """设置值"""
        if self._value != new_value:
            old_value = self._value
            self._value = new_value
            self._notify(old_value, new_value)
    
    def set(self, value: T) -> None:
        """设置值"""
        self.value = value
    
    def get(self) -> T:
        """获取值"""
        return self._value
    
    def subscribe(self, listener: Callable[[T, T], None]) -> Callable:
        """
        订阅变更
        
        Args:
            listener: (old_value, new_value) -> None
            
        Returns:
            取消订阅函数
        """
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)
    
    def _notify(self, old_value: T, new_value: T) -> None:
        """通知订阅者"""
        for listener in self._listeners:
            try:
                listener(old_value, new_value)
            except Exception:
                pass
    
    def __repr__(self) -> str:
        return f"Prop({self._value!r})"


class ComputedProp(Prop[T]):
    """
    计算属性
    
    基于其他属性计算。
    """
    
    def __init__(self, compute: Callable[[], T], *deps: Prop):
        """
        Args:
            compute: 计算函数
            *deps: 依赖的属性
        """
        self._compute = compute
        self._deps = deps
        
        # 初始化
        super().__init__(compute())
        
        # 订阅依赖
        def on_change(old, new):
            self._value = compute()
            self._notify(self._value, self._value)
        
        for dep in deps:
            dep.subscribe(on_change)


class DictProp(Prop[dict]):
    """
    字典属性
    
    支持键路径访问。
    """
    
    def get_path(self, path: str, default: Any = None) -> Any:
        """
        获取嵌套值
        
        Args:
            path: 点分隔路径 (如 "a.b.c")
            default: 默认值
            
        Returns:
            值或默认值
        """
        keys = path.split('.')
        value = self._value
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_path(self, path: str, value: Any) -> None:
        """
        设置嵌套值
        
        Args:
            path: 点分隔路径
            value: 要设置的值
        """
        keys = path.split('.')
        current = self._value
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        old_value = self.get_path(path)
        current[keys[-1]] = value
        self._notify(old_value, value)


# 导出
__all__ = [
    "Prop",
    "ComputedProp",
    "DictProp",
]
