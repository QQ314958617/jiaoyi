"""
Emit - 事件发射
基于 Claude Code emit.ts 设计

事件发射工具。
"""
import asyncio
from typing import Any, Callable, Dict, List
from collections import defaultdict


class Emit:
    """
    事件发射器
    
    支持同步和异步监听器。
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)
        self._once_listeners: Dict[str, List[Callable]] = defaultdict(list)
    
    def on(self, event: str, listener: Callable) -> "Emit":
        """注册监听器"""
        self._listeners[event].append(listener)
        return self
    
    def once(self, event: str, listener: Callable) -> "Emit":
        """注册一次性监听器"""
        self._once_listeners[event].append(listener)
        return self
    
    def off(self, event: str, listener: Callable) -> "Emit":
        """取消监听器"""
        if event in self._listeners:
            try:
                self._listeners[event].remove(listener)
            except ValueError:
                pass
        return self
    
    def emit(self, event: str, *args, **kwargs) -> bool:
        """发射事件"""
        # 执行普通监听器
        listeners = self._listeners.get(event, [])
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    # 同步发射不等待异步监听器
                    pass
                else:
                    listener(*args, **kwargs)
            except Exception:
                pass
        
        # 执行一次性监听器
        once_listeners = self._once_listeners.pop(event, [])
        for listener in once_listeners:
            try:
                listener(*args, **kwargs)
            except Exception:
                pass
        
        return len(listeners) > 0 or len(once_listeners) > 0
    
    async def emit_async(self, event: str, *args, **kwargs) -> bool:
        """异步发射事件"""
        # 执行普通监听器
        listeners = self._listeners.get(event, [])
        tasks = []
        
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    tasks.append(asyncio.create_task(listener(*args, **kwargs)))
                else:
                    listener(*args, **kwargs)
            except Exception:
                pass
        
        # 执行一次性监听器
        once_listeners = self._once_listeners.pop(event, [])
        for listener in once_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    tasks.append(asyncio.create_task(listener(*args, **kwargs)))
                else:
                    listener(*args, **kwargs)
            except Exception:
                pass
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return len(listeners) > 0 or len(once_listeners) > 0
    
    def listener_count(self, event: str) -> int:
        """获取监听器数量"""
        return len(self._listeners.get(event, []))
    
    def event_names(self) -> List[str]:
        """获取所有事件名"""
        return list(set(list(self._listeners.keys()) + list(self._once_listeners.keys())))
    
    def clear(self, event: str = None) -> None:
        """清空监听器"""
        if event:
            self._listeners.pop(event, None)
            self._once_listeners.pop(event, None)
        else:
            self._listeners.clear()
            self._once_listeners.clear()


class EventBus(Emit):
    """
    事件总线
    
    全局事件系统。
    """
    pass


# 全局事件总线
_global_event_bus = EventBus()


def event_bus() -> EventBus:
    """获取全局事件总线"""
    return _global_event_bus


def on(event: str, listener: Callable) -> EventBus:
    """全局注册监听器"""
    return _global_event_bus.on(event, listener)


def once(event: str, listener: Callable) -> EventBus:
    """全局注册一次性监听器"""
    return _global_event_bus.once(event, listener)


def off(event: str, listener: Callable) -> EventBus:
    """全局取消监听器"""
    return _global_event_bus.off(event, listener)


def emit(event: str, *args, **kwargs) -> bool:
    """全局发射事件"""
    return _global_event_bus.emit(event, *args, **kwargs)


# 导出
__all__ = [
    "Emit",
    "EventBus",
    "event_bus",
    "on",
    "once",
    "off",
    "emit",
]
