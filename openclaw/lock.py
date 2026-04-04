"""
Lock - 分布式锁
基于 Claude Code lock.ts 设计

分布式锁实现。
"""
import time
import uuid
from typing import Optional


class Lock:
    """
    简单分布式锁
    
    基于文件锁实现（可用于进程同步）。
    """
    
    def __init__(self, name: str, timeout: float = 10.0):
        """
        Args:
            name: 锁名称
            timeout: 默认超时时间
        """
        self._name = name
        self._timeout = timeout
        self._token = str(uuid.uuid4())
        self._acquired = False
    
    def acquire(self, timeout: float = None) -> bool:
        """
        获取锁
        
        Args:
            timeout: 超时时间
            
        Returns:
            是否成功
        """
        timeout = timeout or self._timeout
        
        start = time.time()
        
        while True:
            try:
                import fcntl
                self._fd = open(f"/tmp/{self._name}.lock", 'w')
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._fd.write(self._token)
                self._fd.flush()
                self._acquired = True
                return True
            except (IOError, OSError):
                if time.time() - start >= timeout:
                    return False
                time.sleep(0.1)
    
    def release(self) -> bool:
        """
        释放锁
        
        Returns:
            是否成功
        """
        if not self._acquired:
            return False
        
        try:
            import fcntl
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            self._fd.close()
            import os
            os.remove(f"/tmp/{self._name}.lock")
            self._acquired = False
            return True
        except Exception:
            return False
    
    def __enter__(self) -> "Lock":
        self.acquire()
        return self
    
    def __exit__(self, *args) -> None:
        self.release()


class Semaphore:
    """
    信号量
    
    控制并发访问数量。
    """
    
    def __init__(self, permits: int = 1):
        """
        Args:
            permits: 许可数量
        """
        import threading
        self._permits = permits
        self._lock = threading.Lock()
    
    def acquire(self, timeout: float = None) -> bool:
        """
        获取许可
        
        Args:
            timeout: 超时时间
            
        Returns:
            是否成功
        """
        start = time.time()
        
        while True:
            with self._lock:
                if self._permits > 0:
                    self._permits -= 1
                    return True
            
            if timeout is not None and time.time() - start >= timeout:
                return False
            
            time.sleep(0.01)
    
    def release(self) -> None:
        """释放许可"""
        with self._lock:
            self._permits += 1
    
    def __enter__(self) -> "Semaphore":
        self.acquire()
        return self
    
    def __exit__(self, *args) -> None:
        self.release()


class ReadWriteLock:
    """
    读写锁
    
    读并行，写独占。
    """
    
    def __init__(self):
        import threading
        self._readers = 0
        self._writers = 0
        self._reader_lock = threading.Lock()
        self._writer_lock = threading.Lock()
        self._prefer_writer = True
    
    def acquire_read(self) -> None:
        """获取读锁"""
        import threading
        while True:
            with self._reader_lock:
                if self._writers == 0:
                    self._readers += 1
                    return
            
            time.sleep(0.01)
    
    def acquire_write(self) -> None:
        """获取写锁"""
        import threading
        with self._writer_lock:
            self._writers += 1
        
        while True:
            with self._reader_lock:
                if self._readers == 0:
                    return
            
            time.sleep(0.01)
    
    def release_read(self) -> None:
        """释放读锁"""
        with self._reader_lock:
            self._readers -= 1
    
    def release_write(self) -> None:
        """释放写锁"""
        with self._writer_lock:
            self._writers -= 1


# 导出
__all__ = [
    "Lock",
    "Semaphore",
    "ReadWriteLock",
]
