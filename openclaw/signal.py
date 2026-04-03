"""
OpenClaw Signal/Event Bus
========================
Inspired by Claude Code's src/utils/signal.ts (56 lines).

轻量级事件信号系统：
- create_signal(): 创建信号
- subscribe(listener): 订阅，返回取消订阅函数
- emit(*args): 触发事件
- clear(): 清空所有监听器

用途：
- 交易信号通知
- 状态变化通知
- 事件解耦
"""

from __future__ import annotations

from typing import Callable, Generic, TypeVar
from dataclasses import dataclass
import threading

T = TypeVar('T')


class Signal:
    """
    事件信号
    
    轻量级发布-订阅模式，无状态存储。
    
    Claude Code 模式：
    ```typescript
    const changed = createSignal<[SettingSource]>()
    export const subscribe = changed.subscribe
    changed.emit('userSettings')
    ```
    
    Python 等效：
    ```python
    trade_signal = Signal()
    unsub = trade_signal.subscribe(lambda action: print(f"Trade: {action}"))
    trade_signal.emit("BUY 600362")
    unsub()  # 取消订阅
    ```
    """
    
    def __init__(self):
        self._listeners: list[Callable] = []
        self._lock = threading.Lock()
    
    def subscribe(self, listener: Callable) -> Callable:
        """
        订阅事件
        
        Returns: 取消订阅函数
        """
        with self._lock:
            self._listeners.append(listener)
        
        def unsubscribe():
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)
        
        return unsubscribe
    
    def emit(self, *args, **kwargs) -> None:
        """触发事件，通知所有订阅者"""
        with self._lock:
            listeners = list(self._listeners)
        
        for listener in listeners:
            try:
                if kwargs:
                    listener(*args, **kwargs)
                else:
                    listener(*args)
            except Exception as e:
                # 订阅者错误不应该中断 emit
                import traceback
                traceback.print_exc()
    
    def clear(self) -> None:
        """清空所有监听器"""
        with self._lock:
            self._listeners.clear()
    
    def count(self) -> int:
        """当前监听器数量"""
        with self._lock:
            return len(self._listeners)


class AsyncSignal:
    """
    异步版本的事件信号
    """
    
    def __init__(self):
        self._listeners: list[Callable] = []
        self._lock = threading.Lock()
    
    async def subscribe(self, listener: Callable) -> Callable:
        """异步订阅"""
        with self._lock:
            self._listeners.append(listener)
        
        def unsubscribe():
            with self._lock:
                if listener in self._listeners:
                    self._listeners.remove(listener)
        
        return unsubscribe
    
    async def emit(self, *args, **kwargs) -> None:
        """异步触发"""
        import asyncio
        
        with self._lock:
            listeners = list(self._listeners)
        
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    if kwargs:
                        await listener(*args, **kwargs)
                    else:
                        await listener(*args)
                else:
                    if kwargs:
                        listener(*args, **kwargs)
                    else:
                        listener(*args)
            except Exception as e:
                import traceback
                traceback.print_exc()
    
    async def clear(self) -> None:
        self._listeners.clear()
    
    def count(self) -> int:
        with self._lock:
            return len(self._listeners)


# ============================================================================
# 全局信号实例
# ============================================================================

# 交易相关信号
trade_executed = Signal()      # 交易执行通知
price_alert = Signal()        # 价格预警
signal_detected = Signal()     # 策略信号检测
market_open = Signal()         # 开盘
market_close = Signal()       # 收盘
error_occurred = Signal()     # 错误发生

# 系统信号
startup_complete = Signal()   # 启动完成
shutdown_requested = Signal() # 关闭请求

# ============================================================================
# 信号管理器
# ============================================================================

class SignalManager:
    """
    全局信号管理器
    
    统一管理所有信号，便于：
    - 调试：查看所有活跃的信号
    - 统计：信号触发次数
    - 清理：一键清空所有信号
    """
    
    def __init__(self):
        self._signals: dict[str, Signal] = {}
        self._counts: dict[str, int] = {}
        self._lock = threading.Lock()
    
    def get(self, name: str) -> Signal:
        """获取或创建信号"""
        with self._lock:
            if name not in self._signals:
                self._signals[name] = Signal()
            return self._signals[name]
    
    def emit(self, name: str, *args, **kwargs) -> None:
        """触发命名信号"""
        with self._lock:
            if name not in self._signals:
                return
            signal = self._signals[name]
            self._counts[name] = self._counts.get(name, 0) + 1
        
        signal.emit(*args, **kwargs)
    
    def subscribe(self, name: str, listener: Callable) -> Callable:
        """订阅命名信号"""
        signal = self.get(name)
        return signal.subscribe(listener)
    
    def clear(self, name: str) -> None:
        """清空命名信号"""
        with self._lock:
            if name in self._signals:
                self._signals[name].clear()
    
    def clear_all(self) -> None:
        """清空所有信号"""
        with self._lock:
            for signal in self._signals.values():
                signal.clear()
            self._counts.clear()
    
    def get_counts(self) -> dict[str, int]:
        """获取信号触发统计"""
        with self._lock:
            return dict(self._counts)
    
    def list_signals(self) -> list[str]:
        """列出所有信号名"""
        with self._lock:
            return list(self._signals.keys())


# 全局实例
_signal_manager: SignalManager | None = None
_manager_lock = threading.Lock()

def get_signal_manager() -> SignalManager:
    """获取全局信号管理器"""
    global _signal_manager
    with _manager_lock:
        if _signal_manager is None:
            _signal_manager = SignalManager()
        return _signal_manager
