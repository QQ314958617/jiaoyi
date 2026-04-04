"""
RateLimit2 - 限流2
基于 Claude Code rateLimit2.ts 设计

令牌桶限流实现。
"""
import asyncio
import time
from threading import Lock


class TokenBucket:
    """
    令牌桶限流器
    
    平滑限流。
    """
    
    def __init__(
        self,
        rate: float,
        capacity: int,
    ):
        """
        Args:
            rate: 每秒补充的令牌数
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
        
        Returns:
            是否成功
        """
        with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
    
    def acquire(self, tokens: int = 1, timeout: float = None) -> bool:
        """
        获取令牌（阻塞）
        
        Args:
            tokens: 令牌数
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
            
            # 计算需要等待的时间
            wait_time = (tokens - self._tokens) / self._rate
            time.sleep(min(wait_time, 0.1))
    
    def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self._last_update
        tokens_to_add = elapsed * self._rate
        
        self._tokens = min(
            self._capacity,
            self._tokens + tokens_to_add
        )
        self._last_update = now


class SlidingWindow:
    """
    滑动窗口限流器
    
    更精确的限流。
    """
    
    def __init__(
        self,
        max_requests: int,
        window_ms: int,
    ):
        """
        Args:
            max_requests: 窗口内最大请求数
            window_ms: 窗口大小（毫秒）
        """
        self._max_requests = max_requests
        self._window_ms = window_ms
        self._requests: list = []
        self._lock = Lock()
    
    def try_acquire(self) -> bool:
        """尝试获取"""
        now = time.time()
        window_start = now - self._window_ms / 1000
        
        with self._lock:
            # 清理过期的请求
            self._requests = [t for t in self._requests if t > window_start]
            
            if len(self._requests) < self._max_requests:
                self._requests.append(now)
                return True
            
            return False
    
    def acquire(self, timeout: float = None) -> bool:
        """获取（阻塞）"""
        start = time.time()
        
        while True:
            if self.try_acquire():
                return True
            
            if timeout is not None and time.time() - start >= timeout:
                return False
            
            time.sleep(0.01)


class LeakyBucket:
    """
    漏桶限流器
    
    固定速率输出。
    """
    
    def __init__(
        self,
        rate: float,
        capacity: int,
    ):
        """
        Args:
            rate: 漏出速率（每秒）
            capacity: 桶容量
        """
        self._rate = rate
        self._capacity = capacity
        self._water = 0.0
        self._last_leak = time.time()
        self._lock = Lock()
    
    def try_add(self, water: float = 1.0) -> bool:
        """尝试加水"""
        with self._lock:
            self._leak()
            
            if self._water + water <= self._capacity:
                self._water += water
                return True
            
            return False
    
    def _leak(self) -> None:
        """漏水"""
        now = time.time()
        elapsed = now - self._last_leak
        leaked = elapsed * self._rate
        
        self._water = max(0, self._water - leaked)
        self._last_leak = now


class MultiRateLimit:
    """
    多维限流器
    
    支持多个限流维度。
    """
    
    def __init__(self):
        self._limiters: dict = {}
        self._lock = Lock()
    
    def add_limiter(self, key: str, limiter) -> None:
        """添加限流器"""
        with self._lock:
            self._limiters[key] = limiter
    
    def check(self, key: str) -> bool:
        """检查限流"""
        with self._lock:
            if key not in self._limiters:
                return True
            return self._limiters[key].try_acquire()


# 导出
__all__ = [
    "TokenBucket",
    "SlidingWindow",
    "LeakyBucket",
    "MultiRateLimit",
]
