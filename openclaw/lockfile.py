"""
Lockfile - 文件锁
基于 Claude Code lockfile.ts 设计

文件锁实现。
"""
import os
import fcntl
import time
from typing import Optional


class Lockfile:
    """
    文件锁封装
    
    使用fcntl实现文件锁。
    """
    
    def __init__(self, file_path: str):
        """
        Args:
            file_path: 锁文件路径
        """
        self.file_path = file_path
        self.fd: Optional[int] = None
        self.lock_file_path = file_path + '.lock'
    
    def acquire(self, timeout: float = 10.0) -> bool:
        """
        获取锁
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            是否成功获取
        """
        start_time = time.time()
        
        while True:
            try:
                # 创建锁文件
                self.fd = os.open(
                    self.lock_file_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                os.write(self.fd, str(os.getpid()).encode())
                os.close(self.fd)
                self.fd = None
                return True
            except FileExistsError:
                # 锁已存在，检查是否过期
                if timeout <= 0:
                    return False
                
                # 等待一下
                time.sleep(0.1)
                timeout -= 0.1
                
                # 检查超时
                if time.time() - start_time >= timeout:
                    return False
    
    def release(self) -> None:
        """释放锁"""
        try:
            if os.path.exists(self.lock_file_path):
                os.remove(self.lock_file_path)
        except Exception:
            pass
    
    def check(self) -> bool:
        """
        检查锁是否存在
        
        Returns:
            锁是否存在
        """
        return os.path.exists(self.lock_file_path)
    
    def __enter__(self) -> "Lockfile":
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


def lock(file_path: str, timeout: float = 10.0) -> bool:
    """
    获取文件锁
    
    Args:
        file_path: 锁文件路径
        timeout: 超时时间
        
    Returns:
        是否成功
    """
    lockfile = Lockfile(file_path)
    return lockfile.acquire(timeout)


def lock_sync(file_path: str, timeout: float = 10.0) -> callable:
    """
    同步获取文件锁
    
    Args:
        file_path: 锁文件路径
        timeout: 超时时间
        
    Returns:
        释放函数
    """
    lockfile = Lockfile(file_path)
    lockfile.acquire(timeout)
    return lockfile.release


def unlock(file_path: str) -> bool:
    """
    释放文件锁
    
    Args:
        file_path: 锁文件路径
        
    Returns:
        是否成功
    """
    try:
        lock_path = file_path + '.lock'
        if os.path.exists(lock_path):
            os.remove(lock_path)
        return True
    except Exception:
        return False


def check(file_path: str) -> bool:
    """
    检查锁是否存在
    
    Args:
        file_path: 锁文件路径
        
    Returns:
        锁是否存在
    """
    return os.path.exists(file_path + '.lock')


# 导出
__all__ = [
    "Lockfile",
    "lock",
    "lock_sync",
    "unlock",
    "check",
]
