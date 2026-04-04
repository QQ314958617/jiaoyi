"""
Observer - 观察者
基于 Claude Code observer.ts 设计

观察者模式工具。
"""
from typing import Any, Callable, Dict, List


class Observer:
    """
    观察者
    
    简单的发布-订阅。
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, handler: Callable) -> "Observer":
        """
        订阅事件
        
        Args:
            event: 事件名
            handler: 处理函数
            
        Returns:
            self
        """
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
        return self
    
    def off(self, event: str, handler: Callable = None) -> "Observer":
        """
        取消订阅
        
        Args:
            event: 事件名
            handler: 处理函数（None则取消所有）
            
        Returns:
            self
        """
        if handler is None:
            self._handlers.pop(event, None)
        elif event in self._handlers:
            try:
                self._handlers[event].remove(handler)
            except ValueError:
                pass
        return self
    
    def emit(self, event: str, *args, **kwargs) -> "Observer":
        """
        发射事件
        
        Args:
            event: 事件名
            *args, **kwargs: 事件数据
            
        Returns:
            self
        """
        for handler in self._handlers.get(event, [])[:]:
            try:
                handler(*args, **kwargs)
            except Exception:
                pass
        return self
    
    def once(self, event: str, handler: Callable) -> "Observer":
        """
        订阅一次
        
        Args:
            event: 事件名
            handler: 处理函数
            
        Returns:
            self
        """
        def wrapper(*args, **kwargs):
            handler(*args, **kwargs)
            self.off(event, wrapper)
        
        return self.on(event, wrapper)
    
    def clear(self, event: str = None) -> "Observer":
        """
        清空
        
        Args:
            event: 事件名（None则清空所有）
            
        Returns:
            self
        """
        if event:
            self._handlers.pop(event, None)
        else:
            self._handlers.clear()
        return self


class Observable:
    """
    可观察对象
    
    支持观察者订阅。
    """
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def add_observer(self, observer: Observer) -> None:
        """添加观察者"""
        self._observers.append(observer)
    
    def remove_observer(self, observer: Observer) -> None:
        """移除观察者"""
        try:
            self._observers.remove(observer)
        except ValueError:
            pass
    
    def notify(self, event: str, *args, **kwargs) -> None:
        """通知所有观察者"""
        for observer in self._observers[:]:
            observer.emit(event, *args, **kwargs)


class PropertyObserver:
    """
    属性观察器
    
    观察对象属性变化。
    """
    
    def __init__(self, target: object):
        """
        Args:
            target: 目标对象
        """
        self._target = target
        self._callbacks: Dict[str, List[Callable]] = {}
        self._values: Dict[str, Any] = {}
        
        # 保存初始值
        for key in dir(target):
            if not key.startswith('_'):
                try:
                    self._values[key] = getattr(target, key)
                except AttributeError:
                    pass
    
    def watch(self, property_name: str, callback: Callable[[Any, Any], None]) -> None:
        """
        监视属性
        
        Args:
            property_name: 属性名
            callback: (old_value, new_value) -> None
        """
        if property_name not in self._callbacks:
            self._callbacks[property_name] = []
        self._callbacks[property_name].append(callback)
    
    def check(self) -> None:
        """检查变化"""
        for key in self._values:
            try:
                current = getattr(self._target, key)
                old = self._values[key]
                
                if current != old:
                    self._values[key] = current
                    
                    for callback in self._callbacks.get(key, []):
                        try:
                            callback(old, current)
                        except Exception:
                            pass
            except AttributeError:
                pass


# 导出
__all__ = [
    "Observer",
    "Observable",
    "PropertyObserver",
]
