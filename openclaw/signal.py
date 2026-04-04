"""
Signal - 信号
基于 Claude Code signal.ts 设计

信号模式实现。
"""
from typing import Any, Callable, Dict, List, Optional


class Signal:
    """
    信号
    
    简单的发布-订阅模式。
    """
    
    def __init__(self):
        self._subscribers: List[Callable] = []
    
    def subscribe(self, callback: Callable) -> Callable:
        """
        订阅信号
        
        Args:
            callback: 回调函数
            
        Returns:
            取消订阅函数
        """
        self._subscribers.append(callback)
        
        def unsubscribe():
            if callback in self._subscribers:
                self._subscribers.remove(callback)
        
        return unsubscribe
    
    def emit(self, *args, **kwargs) -> None:
        """发射信号"""
        for callback in self._subscribers[:]:  # 复制避免修改
            try:
                callback(*args, **kwargs)
            except Exception:
                pass
    
    def once(self, callback: Callable) -> None:
        """订阅一次"""
        def wrapper(*args, **kwargs):
            callback(*args, **kwargs)
            self.unsubscribe(wrapper)
        
        self._subscribers.append(wrapper)
    
    def unsubscribe(self, callback: Callable) -> bool:
        """取消订阅"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            return True
        return False
    
    def clear(self) -> None:
        """清空所有订阅"""
        self._subscribers.clear()
    
    @property
    def count(self) -> int:
        """订阅者数量"""
        return len(self._subscribers)


class SignalMap:
    """
    信号映射
    
    管理多个命名信号。
    """
    
    def __init__(self):
        self._signals: Dict[str, Signal] = {}
    
    def get(self, name: str) -> Signal:
        """获取或创建信号"""
        if name not in self._signals:
            self._signals[name] = Signal()
        return self._signals[name]
    
    def emit(self, name: str, *args, **kwargs) -> None:
        """发射命名信号"""
        if name in self._signals:
            self._signals[name].emit(*args, **kwargs)
    
    def subscribe(self, name: str, callback: Callable) -> Callable:
        """订阅命名信号"""
        return self.get(name).subscribe(callback)
    
    def delete(self, name: str) -> bool:
        """删除信号"""
        if name in self._signals:
            del self._signals[name]
            return True
        return False


class Emitter:
    """
    事件发射器
    
    支持通配符和命名空间。
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, callback: Callable) -> Callable:
        """
        监听事件
        
        Args:
            event: 事件名
            callback: 回调
            
        Returns:
            取消监听函数
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        
        return lambda: self.off(event, callback)
    
    def off(self, event: str, callback: Callable) -> bool:
        """取消监听"""
        if event in self._listeners:
            if callback in self._listeners[event]:
                self._listeners[event].remove(callback)
                return True
        return False
    
    def emit(self, event: str, *args, **kwargs) -> None:
        """发射事件"""
        # 精确匹配
        for callback in self._listeners.get(event, [])[:]:
            try:
                callback(*args, **kwargs)
            except Exception:
                pass
        
        # 通配符匹配
        for pattern, callbacks in self._listeners.items():
            if pattern != event and self._match(event, pattern):
                for callback in callbacks[:]:
                    try:
                        callback(*args, **kwargs)
                    except Exception:
                        pass
    
    def _match(self, event: str, pattern: str) -> bool:
        """通配符匹配"""
        import re
        regex = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.match(f'^{regex}$', event))
    
    def once(self, event: str, callback: Callable) -> None:
        """一次监听"""
        def wrapper(*args, **kwargs):
            callback(*args, **kwargs)
            self.off(event, wrapper)
        
        self.on(event, wrapper)


# 导出
__all__ = [
    "Signal",
    "SignalMap",
    "Emitter",
]
