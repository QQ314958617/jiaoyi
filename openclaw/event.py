"""
Event - 事件
基于 Claude Code event.ts 设计

事件系统工具。
"""
from typing import Any, Callable, Dict, List


class Event:
    """
    事件
    """
    
    def __init__(self, name: str):
        """
        Args:
            name: 事件名称
        """
        self._name = name
        self._listeners: List[Callable] = []
    
    def on(self, listener: Callable) -> Callable:
        """
        订阅
        
        Args:
            listener: 监听函数
            
        Returns:
            取消订阅函数
        """
        self._listeners.append(listener)
        return lambda: self.off(listener)
    
    def off(self, listener: Callable) -> None:
        """取消订阅"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def once(self, listener: Callable) -> Callable:
        """
        单次订阅
        
        Args:
            listener: 监听函数
            
        Returns:
            取消订阅函数
        """
        def wrapper(*args, **kwargs):
            listener(*args, **kwargs)
            self.off(wrapper)
        
        return self.on(wrapper)
    
    def emit(self, *args, **kwargs) -> None:
        """
        触发事件
        """
        for listener in list(self._listeners):
            try:
                listener(*args, **kwargs)
            except Exception:
                pass
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def listener_count(self) -> int:
        return len(self._listeners)


class EventEmitter:
    """
    事件发射器
    """
    
    def __init__(self):
        self._events: Dict[str, Event] = {}
    
    def on(self, event_name: str, listener: Callable) -> Callable:
        """
        订阅事件
        
        Args:
            event_name: 事件名
            listener: 监听函数
            
        Returns:
            取消订阅函数
        """
        event = self._events.get(event_name)
        if not event:
            event = Event(event_name)
            self._events[event_name] = event
        return event.on(listener)
    
    def off(self, event_name: str, listener: Callable) -> None:
        """取消订阅"""
        event = self._events.get(event_name)
        if event:
            event.off(listener)
    
    def once(self, event_name: str, listener: Callable) -> Callable:
        """单次订阅"""
        event = self._events.get(event_name)
        if not event:
            event = Event(event_name)
            self._events[event_name] = event
        return event.once(listener)
    
    def emit(self, event_name: str, *args, **kwargs) -> None:
        """触发事件"""
        event = self._events.get(event_name)
        if event:
            event.emit(*args, **kwargs)
    
    def clear(self, event_name: str = None) -> None:
        """清空事件"""
        if event_name:
            self._events.pop(event_name, None)
        else:
            self._events.clear()
    
    def event_names(self) -> List[str]:
        """获取所有事件名"""
        return list(self._events.keys())


# 便捷函数
def create_event(name: str) -> Event:
    """创建事件"""
    return Event(name)


def create_emitter() -> EventEmitter:
    """创建事件发射器"""
    return EventEmitter()


# 导出
__all__ = [
    "Event",
    "EventEmitter",
    "create_event",
    "create_emitter",
]
