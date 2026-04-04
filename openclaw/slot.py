"""
Slot - 插槽
基于 Claude Code slot.ts 设计

插槽事件工具。
"""
from typing import Any, Callable, Dict, List


class Slot:
    """
    插槽事件系统
    
    简单的发布-订阅。
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, listener: Callable) -> Callable:
        """
        订阅事件
        
        Args:
            event: 事件名
            listener: 监听函数
            
        Returns:
            取消订阅函数
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(listener)
        
        return lambda: self.off(event, listener)
    
    def off(self, event: str, listener: Callable) -> None:
        """取消订阅"""
        if event in self._listeners:
            try:
                self._listeners[event].remove(listener)
            except ValueError:
                pass
    
    def once(self, event: str, listener: Callable) -> Callable:
        """
        单次订阅
        
        Args:
            event: 事件名
            listener: 监听函数
            
        Returns:
            取消订阅函数
        """
        def wrapper(*args, **kwargs):
            listener(*args, **kwargs)
            self.off(event, wrapper)
        
        return self.on(event, wrapper)
    
    def emit(self, event: str, *args, **kwargs) -> None:
        """
        触发事件
        
        Args:
            event: 事件名
            *args, **kwargs: 事件数据
        """
        if event in self._listeners:
            for listener in list(self._listeners[event]):
                try:
                    listener(*args, **kwargs)
                except Exception:
                    pass
    
    def clear(self, event: str = None) -> None:
        """
        清空监听
        
        Args:
            event: 事件名（None表示全部）
        """
        if event:
            self._listeners.pop(event, None)
        else:
            self._listeners.clear()
    
    def listeners(self, event: str) -> List[Callable]:
        """获取事件的所有监听器"""
        return list(self._listeners.get(event, []))
    
    def count(self, event: str) -> int:
        """获取监听器数量"""
        return len(self._listeners.get(event, []))


class EventBus(Slot):
    """事件总线"""
    
    def __init__(self):
        super().__init__()
        self._global_listeners: List[Callable] = []
    
    def on_any(self, listener: Callable) -> Callable:
        """
        监听所有事件
        
        Returns:
            取消订阅函数
        """
        self._global_listeners.append(listener)
        return lambda: self._global_listeners.remove(listener)
    
    def emit(self, event: str, *args, **kwargs) -> None:
        """触发事件（包括全局监听器）"""
        # 全局监听器
        for listener in list(self._global_listeners):
            try:
                listener(event, *args, **kwargs)
            except Exception:
                pass
        
        # 特定事件监听器
        super().emit(event, *args, **kwargs)


# 导出
__all__ = [
    "Slot",
    "EventBus",
]
