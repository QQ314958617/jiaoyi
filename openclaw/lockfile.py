"""
OpenClaw Lockfile
================
Inspired by Claude Code's src/utils/lockfile.ts (lazy accessor for proper-lockfile).

文件锁实现，支持：
1. 尝试获取锁（非阻塞）
2. 等待获取锁（阻塞）
3. 自动释放
4. 锁检查

用途：
- 多进程访问同一个文件
- 防止重复运行
- 配置文件互斥访问
"""

from __future__ import annotations

import fcntl, os, threading, time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ============================================================================
# 文件锁异常
# ============================================================================

class LockfileError(Exception):
    """文件锁错误"""
    pass

class LockfileAcquireError(LockfileError):
    """获取锁失败"""
    pass

class LockfileReleaseError(LockfileError):
    """释放锁失败"""
    pass

# ============================================================================
# 文件锁
# ============================================================================

class FileLock:
    """
    文件锁
    
    基于 fcntl.flock（Unix）或 threading.Lock
    
    特性：
    - 非阻塞获取（try_lock）
    - 阻塞获取（lock）
    - 自动释放（上下文管理器）
    - 进程安全
    
    用途：
    - 防止重复运行
    - 多进程配置文件访问
    """
    
    def __init__(self, lock_file: str, timeout: float = 10.0):
        self.lock_file = lock_file
        self.timeout = timeout
        self._locked = False
        self._lock_fd: Optional[int] = None
        self._lock_type = ""
    
    def _get_lock_path(self) -> str:
        """获取锁文件路径"""
        return self.lock_file + ".lock"
    
    def try_lock(self) -> bool:
        """
        尝试获取锁（非阻塞）
        
        Returns: 是否成功获取锁
        """
        lock_path = self._get_lock_path()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(lock_path) or ".", exist_ok=True)
        
        try:
            # 打开锁文件
            fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
            
            # 非阻塞锁
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._locked = True
                self._lock_fd = fd
                self._lock_type = "exclusive"
                
                # 写入 PID
                os.write(fd, str(os.getpid()).encode())
                os.fsync(fd)
                
                return True
                
            except (IOError, OSError):
                # 锁被占用
                os.close(fd)
                return False
                
        except (IOError, OSError) as e:
            raise LockfileAcquireError(f"Failed to acquire lock: {e}") from e
    
    def lock(self) -> bool:
        """
        获取锁（阻塞）
        
        Returns: 是否成功
        """
        start = time.time()
        
        while True:
            if self.try_lock():
                return True
            
            # 检查超时
            elapsed = time.time() - start
            if elapsed >= self.timeout:
                raise LockfileAcquireError(
                    f"Timeout after {self.timeout}s waiting for lock: {self.lock_file}"
                )
            
            # 等待后重试
            time.sleep(0.1)
    
    def unlock(self) -> None:
        """释放锁"""
        if not self._locked:
            return
        
        try:
            if self._lock_fd is not None:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
                self._lock_fd = None
            
            # 删除锁文件
            lock_path = self._get_lock_path()
            if os.path.exists(lock_path):
                os.unlink(lock_path)
            
            self._locked = False
            
        except (IOError, OSError) as e:
            raise LockfileReleaseError(f"Failed to release lock: {e}") from e
    
    def is_locked(self) -> bool:
        """检查是否已锁定"""
        if self._locked:
            return True
        
        lock_path = self._get_lock_path()
        if not os.path.exists(lock_path):
            return False
        
        # 检查锁文件是否有效
        try:
            fd = os.open(lock_path, os.O_RDWR)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                # 能获取说明锁已释放
                return False
            except (IOError, OSError):
                os.close(fd)
                return True
        except (IOError, OSError):
            return False
    
    def __enter__(self) -> 'FileLock':
        self.lock()
        return self
    
    def __exit__(self, *args) -> None:
        self.unlock()
    
    def __del__(self) -> None:
        if self._locked:
            self.unlock()


class FileLockManager:
    """
    文件锁管理器
    
    管理多个锁，支持：
    - 按名称获取锁
    - 防止重复获取同一锁
    - 自动清理
    """
    
    def __init__(self):
        self._locks: dict[str, FileLock] = {}
        self._lock = threading.Lock()
    
    def acquire(self, name: str, lock_file: Optional[str] = None, 
                timeout: float = 10.0) -> FileLock:
        """获取锁"""
        with self._lock:
            if name in self._locks:
                lock = self._locks[name]
                if lock.is_locked():
                    raise LockfileError(f"Lock '{name}' is already held")
                return lock
            
            lock_file = lock_file or f"/tmp/openclaw.{name}.lock"
            lock = FileLock(lock_file, timeout)
            lock.lock()
            self._locks[name] = lock
            return lock
    
    def release(self, name: str) -> None:
        """释放锁"""
        with self._lock:
            if name in self._locks:
                self._locks[name].unlock()
                del self._locks[name]
    
    def release_all(self) -> None:
        """释放所有锁"""
        with self._lock:
            for lock in list(self._locks.values()):
                lock.unlock()
            self._locks.clear()


# ============================================================================
# 便捷函数
# ============================================================================

_lock_manager: Optional[FileLockManager] = None
_manager_lock = threading.Lock()

def get_lock_manager() -> FileLockManager:
    """获取全局锁管理器"""
    global _lock_manager
    with _manager_lock:
        if _lock_manager is None:
            _lock_manager = FileLockManager()
        return _lock_manager

@contextmanager
def lock(name: str, lock_file: Optional[str] = None, timeout: float = 10.0):
    """
    上下文管理器方式的锁
    
    用法：
    ```python
    with lock("my-task"):
        # 临界区
        ...
    ```
    """
    lock = FileLock(lock_file or f"/tmp/openclaw.{name}.lock", timeout)
    try:
        lock.lock()
        yield lock
    finally:
        lock.unlock()

def check_lock(lock_file: str) -> bool:
    """
    检查锁是否被占用
    
    Returns: True if locked, False otherwise
    """
    lock = FileLock(lock_file)
    return lock.is_locked()
