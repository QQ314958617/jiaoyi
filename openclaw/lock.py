"""
Lock - 锁
基于 Claude Code lock.ts 设计

同步锁工具。
"""
import asyncio
import threading
from typing import Optional


class Lock:
    """
    同步锁
    """
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def acquire(self, blocking: bool = True, timeout: float = None) -> bool:
        """获取锁"""
        return self._lock.acquire(blocking=blocking, timeout=timeout)
    
    def release(self) -> None:
        """释放锁"""
        self._lock.release()
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, *args):
        self.release()


class RLock:
    """
    可重入锁
    """
    
    def __init__(self):
        self._lock = threading.RLock()
    
    def acquire(self, blocking: bool = True, timeout: float = None) -> bool:
        return self._lock.acquire(blocking=blocking, timeout=timeout)
    
    def release(self) -> None:
        self._lock.release()
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, *args):
        self.release()


class Event:
    """
    事件
    """
    
    def __init__(self):
        self._event = threading.Event()
    
    def set(self) -> None:
        self._event.set()
    
    def clear(self) -> None:
        self._event.clear()
    
    def wait(self, timeout: float = None) -> bool:
        return self._event.wait(timeout=timeout)
    
    def is_set(self) -> bool:
        return self._event.is_set()


class Condition:
    """
    条件变量
    """
    
    def __init__(self, lock: Lock = None):
        self._cond = threading.Condition(lock._lock if lock else None)
    
    def wait(self, timeout: float = None) -> bool:
        return self._cond.wait(timeout=timeout)
    
    def notify(self, n: int = 1) -> None:
        self._cond.notify(n)
    
    def notify_all(self) -> None:
        self._cond.notify_all()
    
    def __enter__(self):
        self._cond.acquire()
        return self
    
    def __exit__(self, *args):
        self._cond.release()


class Semaphore:
    """
    信号量
    """
    
    def __init__(self, value: int = 1):
        self._sem = threading.Semaphore(value)
    
    def acquire(self, blocking: bool = True, timeout: float = None) -> bool:
        return self._sem.acquire(blocking=blocking, timeout=timeout)
    
    def release(self) -> None:
        self._sem.release()
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, *args):
        self.release()


class BoundedSemaphore(Semaphore):
    """有界信号量"""
    
    def __init__(self, value: int = 1):
        self._sem = threading.BoundedSemaphore(value)


class AsyncLock:
    """异步锁"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        return await self._lock.acquire()
    
    def release(self):
        self._lock.release()
    
    async def __aenter__(self):
        await self._lock.acquire()
        return self
    
    async def __aexit__(self, *args):
        self.release()


# 导出
__all__ = [
    "Lock",
    "RLock", 
    "Event",
    "Condition",
    "Semaphore",
    "BoundedSemaphore",
    "AsyncLock",
]
