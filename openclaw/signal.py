"""
Signal - 信号/事件系统
基于 Claude Code signal.ts 设计

简单的发布-订阅信号系统，用于事件通知。
"""
import threading
from typing import Callable, Generic, TypeVar
from dataclasses import dataclass


T = TypeVar('T')


@dataclass
class Signal(Generic[T]):
    """信号接口"""
    subscribe: Callable[[Callable[..., None]], Callable[[], None]]
    emit: Callable[..., None]
    clear: Callable[[], None]


class SignalImpl(Generic[T]):
    """
    信号实现
    
    提供发布-订阅模式，用于事件通知。
    """
    
    def __init__(self):
        self._listeners: list[Callable[..., None]] = []
        self._lock = threading.Lock()
    
    def subscribe(self, listener: Callable[..., None]) -> Callable[[], None]:
        """
        订阅信号
        
        Args:
            listener: 监听函数
            
        Returns:
            取消订阅函数
        """
        with self._lock:
            self._listeners.append(listener)
        
        def unsubscribe():
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)
        
        return unsubscribe
    
    def emit(self, *args, **kwargs) -> None:
        """
        触发信号
        
        Args:
            *args, **kwargs: 传递给监听函数的参数
        """
        with self._lock:
            listeners = list(self._listeners)
        
        for listener in listeners:
            try:
                listener(*args, **kwargs)
            except Exception:
                # 忽略监听器中的错误
                pass
    
    def clear(self) -> None:
        """清除所有监听器"""
        with self._lock:
            self._listeners.clear()
    
    def __len__(self) -> int:
        """获取监听器数量"""
        with self._lock:
            return len(self._listeners)


def create_signal() -> Signal:
    """
    创建信号
    
    Returns:
        Signal对象
    """
    impl = SignalImpl()
    return Signal(
        subscribe=impl.subscribe,
        emit=impl.emit,
        clear=impl.clear,
    )


class SignalFactory:
    """
    信号工厂
    
    用于创建类型安全的信号。
    """
    
    @staticmethod
    def create() -> Signal:
        """创建无参数信号"""
        return create_signal()


# 导出
__all__ = [
    "Signal",
    "SignalImpl",
    "create_signal",
    "SignalFactory",
]
