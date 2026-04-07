"""
State Store - 状态存储核心
从 Claude Code src/state/store.ts 移植

核心模式：发布-订阅状态容器
- getState() 获取当前状态
- setState(updater) 更新状态（函数式）
- subscribe(listener) 订阅变更，返回取消订阅函数

优点：
- 线程安全
- 状态不可变更新
- 精确订阅（只订阅关心的字段）
- React useSyncExternalStore 模式
"""
import threading
from typing import Callable, Dict, Generic, TypeVar, Optional, Any
from dataclasses import dataclass

T = TypeVar("T")


class Store(Generic[T]):
    """
    状态存储 - 核心组件

    用法：
    1. 创建存储
    2. 订阅变更
    3. 更新状态
    """

    def __init__(self, initial_state: T):
        self._state = initial_state
        self._listeners: Dict[int, Callable[[], None]] = {}
        self._lock = threading.Lock()
        self._listener_counter = 0

    def get_state(self) -> T:
        """获取当前状态"""
        return self._state

    def set_state(self, updater: Callable[[T], T]) -> None:
        """
        更新状态
        updater: 接收旧状态，返回新状态
        """
        with self._lock:
            prev = self._state
            next_state = updater(prev)
            # 严格相等检查，避免不必要的更新
            if next_state is prev:
                return
            self._state = next_state
            old = prev
            new = next_state

        # 通知所有监听器
        for listener in list(self._listeners.values()):
            try:
                listener()
            except Exception as e:
                print(f"[Store] Listener error: {e}")

    def subscribe(self, listener: Callable[[], None]) -> Callable[[], None]:
        """
        订阅状态变更
        返回取消订阅函数
        """
        with self._lock:
            self._listener_counter += 1
            listener_id = self._listener_counter
            self._listeners[listener_id] = listener

        def unsubscribe():
            with self._lock:
                self._listeners.pop(listener_id, None)

        return unsubscribe

    @property
    def state(self) -> T:
        """属性方式获取状态（别名）"""
        return self.get_state()


def create_store(initial_state: T) -> Store[T]:
    """创建状态存储的便捷函数"""
    return Store(initial_state)
