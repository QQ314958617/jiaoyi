"""
Events - 事件系统
基于 Claude Code events.ts 设计

简单的事件发射器/监听器系统。
"""
from typing import Callable, Dict, List, Any
import threading


class EventEmitter:
    """
    事件发射器
    
    提供发布-订阅模式的事件处理。
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._once_listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()
    
    def on(self, event: str, listener: Callable) -> Callable:
        """
        注册事件监听器
        
        Args:
            event: 事件名
            listener: 监听函数
            
        Returns:
            取消注册函数
        """
        with self._lock:
            if event not in self._listeners:
                self._listeners[event] = []
            self._listeners[event].append(listener)
        
        def remove():
            self.off(event, listener)
        
        return remove
    
    def once(self, event: str, listener: Callable) -> Callable:
        """
        注册一次性监听器
        
        Args:
            event: 事件名
            listener: 监听函数
            
        Returns:
            取消注册函数
        """
        with self._lock:
            if event not in self._once_listeners:
                self._once_listeners[event] = []
            self._once_listeners[event].append(listener)
        
        def remove():
            self.off_once(event, listener)
        
        return remove
    
    def off(self, event: str, listener: Callable) -> None:
        """
        取消注册监听器
        
        Args:
            event: 事件名
            listener: 监听函数
        """
        with self._lock:
            if event in self._listeners:
                if listener in self._listeners[event]:
                    self._listeners[event].remove(listener)
    
    def off_once(self, event: str, listener: Callable) -> None:
        """
        取消注册一次性监听器
        
        Args:
            event: 事件名
            listener: 监听函数
        """
        with self._lock:
            if event in self._once_listeners:
                if listener in self._once_listeners[event]:
                    self._once_listeners[event].remove(listener)
    
    def emit(self, event: str, *args, **kwargs) -> None:
        """
        发射事件
        
        Args:
            event: 事件名
            *args, **kwargs: 传递给监听器的参数
        """
        # 复制监听器列表避免修改冲突
        with self._lock:
            listeners = list(self._listeners.get(event, []))
            once_listeners = list(self._once_listeners.get(event, []))
        
        # 调用普通监听器
        for listener in listeners:
            try:
                listener(*args, **kwargs)
            except Exception:
                pass
        
        # 调用一次性监听器并清除
        for listener in once_listeners:
            try:
                listener(*args, **kwargs)
            except Exception:
                pass
        
        if once_listeners:
            with self._lock:
                if event in self._once_listeners:
                    for listener in once_listeners:
                        if listener in self._once_listeners[event]:
                            self._once_listeners[event].remove(listener)
    
    def clear(self, event: str = None) -> None:
        """
        清除监听器
        
        Args:
            event: 事件名，None表示清除所有
        """
        with self._lock:
            if event is None:
                self._listeners.clear()
                self._once_listeners.clear()
            else:
                self._listeners.pop(event, None)
                self._once_listeners.pop(event, None)
    
    def listener_count(self, event: str) -> int:
        """
        获取监听器数量
        
        Args:
            event: 事件名
            
        Returns:
            监听器数量
        """
        with self._lock:
            return len(self._listeners.get(event, [])) + len(self._once_listeners.get(event, []))


# 全局事件发射器
_global_emitter = EventEmitter()


def get_event_emitter() -> EventEmitter:
    """获取全局事件发射器"""
    return _global_emitter


def on(event: str, listener: Callable) -> Callable:
    """全局on注册"""
    return _global_emitter.on(event, listener)


def once(event: str, listener: Callable) -> Callable:
    """全局once注册"""
    return _global_emitter.once(event, listener)


def off(event: str, listener: Callable) -> None:
    """全局off取消"""
    _global_emitter.off(event, listener)


def emit(event: str, *args, **kwargs) -> None:
    """全局emit发射"""
    _global_emitter.emit(event, *args, **kwargs)


# 导出
__all__ = [
    "EventEmitter",
    "get_event_emitter",
    "on",
    "once",
    "off",
    "emit",
]
