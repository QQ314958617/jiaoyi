"""
Broadcast - 广播
基于 Claude Code broadcast.ts 设计

广播工具。
"""
from typing import Any, Callable, Dict, List


class Broadcast:
    """
    广播
    
    一对多通信。
    """
    
    def __init__(self):
        self._channels: Dict[str, List[Callable]] = {}
    
    def subscribe(self, channel: str, listener: Callable) -> Callable:
        """
        订阅频道
        
        Args:
            channel: 频道名
            listener: 监听函数
            
        Returns:
            取消订阅函数
        """
        if channel not in self._channels:
            self._channels[channel] = []
        self._channels[channel].append(listener)
        
        return lambda: self.unsubscribe(channel, listener)
    
    def unsubscribe(self, channel: str, listener: Callable) -> None:
        """取消订阅"""
        if channel in self._channels:
            try:
                self._channels[channel].remove(listener)
            except ValueError:
                pass
            if not self._channels[channel]:
                del self._channels[channel]
    
    def emit(self, channel: str, *args, **kwargs) -> None:
        """
        发送广播
        
        Args:
            channel: 频道名
            *args, **kwargs: 消息数据
        """
        if channel in self._channels:
            for listener in list(self._channels[channel]):
                try:
                    listener(*args, **kwargs)
                except Exception:
                    pass
    
    def channels(self) -> List[str]:
        """所有频道"""
        return list(self._channels.keys())
    
    def subscriber_count(self, channel: str) -> int:
        """订阅者数量"""
        return len(self._channels.get(channel, []))
    
    def clear(self, channel: str = None) -> None:
        """清空"""
        if channel:
            self._channels.pop(channel, None)
        else:
            self._channels.clear()


class PubSub:
    """
    发布订阅
    """
    
    def __init__(self):
        self._broadcast = Broadcast()
    
    def subscribe(self, channel: str, listener: Callable) -> Callable:
        return self._broadcast.subscribe(channel, listener)
    
    def unsubscribe(self, channel: str, listener: Callable) -> None:
        self._broadcast.unsubscribe(channel, listener)
    
    def publish(self, channel: str, *args, **kwargs) -> None:
        self._broadcast.emit(channel, *args, **kwargs)
    
    def once(self, channel: str, listener: Callable) -> Callable:
        """
        单次订阅
        
        Args:
            channel: 频道名
            listener: 监听函数
        """
        def wrapper(*args, **kwargs):
            listener(*args, **kwargs)
            self.unsubscribe(channel, wrapper)
        
        return self.subscribe(channel, wrapper)


# 别名
class EventBus(Broadcast):
    """事件总线（Broadcast别名）"""
    pass


# 导出
__all__ = [
    "Broadcast",
    "PubSub",
    "EventBus",
]
