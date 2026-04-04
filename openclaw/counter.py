"""
Counter - 计数器
基于 Claude Code counter.ts 设计

线程安全的计数器。
"""
import threading
from typing import Dict


class Counter:
    """
    线程安全计数器
    """
    
    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()
    
    def increment(self, delta: int = 1) -> int:
        """递增"""
        with self._lock:
            self._value += delta
            return self._value
    
    def decrement(self, delta: int = 1) -> int:
        """递减"""
        with self._lock:
            self._value -= delta
            return self._value
    
    def get(self) -> int:
        """获取当前值"""
        with self._lock:
            return self._value
    
    def set(self, value: int) -> None:
        """设置值"""
        with self._lock:
            self._value = value
    
    def reset(self) -> int:
        """重置并返回旧值"""
        with self._lock:
            old = self._value
            self._value = 0
            return old
    
    def __int__(self) -> int:
        return self.get()
    
    def __iadd__(self, delta: int) -> "Counter":
        self.increment(delta)
        return self


class MultiCounter:
    """
    多键计数器
    
    支持多个独立计数器。
    """
    
    def __init__(self):
        self._counters: Dict[str, Counter] = {}
        self._lock = threading.Lock()
    
    def get_counter(self, name: str) -> Counter:
        """获取命名计数器"""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter()
            return self._counters[name]
    
    def increment(self, name: str, delta: int = 1) -> int:
        """递增指定计数器"""
        return self.get_counter(name).increment(delta)
    
    def decrement(self, name: str, delta: int = 1) -> int:
        """递减指定计数器"""
        return self.get_counter(name).decrement(delta)
    
    def get(self, name: str) -> int:
        """获取计数器值"""
        return self.get_counter(name).get()
    
    def reset(self, name: str) -> int:
        """重置指定计数器"""
        return self.get_counter(name).reset()
    
    def names(self) -> list:
        """获取所有计数器名称"""
        with self._lock:
            return list(self._counters.keys())


# 导出
__all__ = [
    "Counter",
    "MultiCounter",
]
