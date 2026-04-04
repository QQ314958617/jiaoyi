"""
Observable - 可观察对象
基于 Claude Code observable.ts 设计

响应式工具。
"""
from typing import Any, Callable, List


class Observable:
    """
    可观察对象
    """
    
    def __init__(self, value: Any = None):
        """
        Args:
            value: 初始值
        """
        self._value = value
        self._observers: List[Callable] = []
    
    @property
    def value(self) -> Any:
        return self._value
    
    @value.setter
    def value(self, new_value: Any) -> None:
        """设置值并通知观察者"""
        if self._value != new_value:
            old_value = self._value
            self._value = new_value
            self._notify(old_value, new_value)
    
    def subscribe(self, observer: Callable) -> Callable:
        """
        订阅
        
        Args:
            observer: 观察函数 (old_value, new_value) -> None
            
        Returns:
            取消订阅函数
        """
        self._observers.append(observer)
        return lambda: self.unsubscribe(observer)
    
    def unsubscribe(self, observer: Callable) -> None:
        """取消订阅"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def _notify(self, old_value: Any, new_value: Any) -> None:
        """通知所有观察者"""
        for observer in list(self._observers):
            try:
                observer(old_value, new_value)
            except Exception:
                pass
    
    def peek(self) -> Any:
        """查看值（不触发订阅）"""
        return self._value


class Computed(Observable):
    """
    计算属性
    """
    
    def __init__(self, compute: Callable, *dependencies):
        """
        Args:
            compute: 计算函数
            *dependencies: 依赖的Observable
        """
        self._compute = compute
        self._dependencies = dependencies
        
        super().__init__(compute())
        
        for dep in dependencies:
            dep.subscribe(self._recompute)
    
    def _recompute(self, old_value, new_value) -> None:
        """重新计算"""
        self.value = self._compute()


class Reaction:
    """
    反应
    
    在值变化时执行副作用。
    """
    
    def __init__(self, fn: Callable, observable: Observable):
        """
        Args:
            fn: 副作用函数
            observable: 观察的可观察对象
        """
        self._fn = fn
        self._observable = observable
        self._dispose: Callable = None
    
    def start(self) -> None:
        """启动反应"""
        def reaction_fn(old_value, new_value):
            self._fn(new_value)
        
        self._dispose = self._observable.subscribe(reaction_fn)
        self._fn(self._observable.value)
    
    def stop(self) -> None:
        """停止反应"""
        if self._dispose:
            self._dispose()
            self._dispose = None


# 导出
__all__ = [
    "Observable",
    "Computed",
    "Reaction",
]
