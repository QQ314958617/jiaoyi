"""
Limiter - 限流器
基于 Claude Code limiter.ts 设计

速率限制工具。
"""
import time
from threading import Lock


class Limiter:
    """
    速率限流器
    
    基于令牌桶算法。
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: 每秒添加的令牌数
            capacity: 桶容量
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last_update = time.time()
        self._lock = Lock()
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """
        尝试获取令牌
        
        Args:
            tokens: 要获取的令牌数
            
        Returns:
            是否成功
        """
        with self._lock:
            now = time.time()
            elapsed = now - self._last_update
            self._tokens = min(
                self._capacity,
                self._tokens + elapsed * self._rate
            )
            self._last_update = now
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
    
    def acquire(self, tokens: int = 1, timeout: float = None) -> bool:
        """
        获取令牌（阻塞）
        
        Args:
            tokens: 要获取的令牌数
            timeout: 超时秒数
            
        Returns:
            是否成功
        """
        start = time.time()
        
        while True:
            if self.try_acquire(tokens):
                return True
            
            if timeout is not None and time.time() - start >= timeout:
                return False
            
            time.sleep(0.01)


class MultiLimiter:
    """
    多键限流器
    
    每个键有独立的限流。
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: 每秒添加的令牌数
            capacity: 桶容量
        """
        self._rate = rate
        self._capacity = capacity
        self._limiters: dict = {}
        self._lock = Lock()
    
    def _get_limiter(self, key: str) -> Limiter:
        """获取键的限流器"""
        with self._lock:
            if key not in self._limiters:
                self._limiters[key] = Limiter(self._rate, self._capacity)
            return self._limiters[key]
    
    def try_acquire(self, key: str, tokens: int = 1) -> bool:
        """尝试获取"""
        return self._get_limiter(key).try_acquire(tokens)
    
    def acquire(self, key: str, tokens: int = 1, timeout: float = None) -> bool:
        """获取（阻塞）"""
        return self._get_limiter(key).acquire(tokens, timeout)


# 导出
__all__ = [
    "Limiter",
    "MultiLimiter",
]
