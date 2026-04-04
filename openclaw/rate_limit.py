"""
Rate Limit - 限流器
基于 Claude Code rateLimit.ts 设计

令牌桶和滑动窗口限流实现。
"""
import time
import threading
from typing import Optional


class TokenBucket:
    """
    令牌桶限流器
    
    以固定速率生成令牌，获取令牌后才能执行操作。
    """
    
    def __init__(
        self,
        rate: float,  # 每秒生成的令牌数
        capacity: int,  # 桶容量
    ):
        """
        Args:
            rate: 每秒生成的令牌数
            capacity: 最大令牌数
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = float(capacity)
        self._last_update = time.time()
        self._lock = threading.Lock()
    
    def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self._last_update
        self._tokens = min(
            self._capacity,
            self._tokens + elapsed * self._rate
        )
        self._last_update = now
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """
        尝试获取令牌
        
        Args:
            tokens: 要获取的令牌数
            
        Returns:
            是否成功获取
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
            tokens: 要获取的令牌数
            timeout: 超时秒数，None表示无限等待
            
        Returns:
            是否成功获取
        """
        start_time = time.time()
        
        while True:
            if self.try_acquire(tokens):
                return True
            
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            # 等待一小段时间
            time.sleep(0.01)
    
    @property
    def available_tokens(self) -> float:
        """当前可用令牌数"""
        with self._lock:
            self._refill()
            return self._tokens


class SlidingWindow:
    """
    滑动窗口限流器
    
    在滑动时间窗口内限制操作次数。
    """
    
    def __init__(
        self,
        max_requests: int,  # 窗口内最大请求数
        window_size_seconds: float,  # 窗口大小（秒）
    ):
        """
        Args:
            max_requests: 窗口内最大请求数
            window_size_seconds: 窗口大小
        """
        self._max_requests = max_requests
        self._window_size = window_size_seconds
        self._requests: list = []
        self._lock = threading.Lock()
    
    def try_acquire(self) -> bool:
        """
        尝试执行操作
        
        Returns:
            是否允许执行
        """
        with self._lock:
            now = time.time()
            cutoff = now - self._window_size
            
            # 移除窗口外的请求
            self._requests = [t for t in self._requests if t > cutoff]
            
            if len(self._requests) < self._max_requests:
                self._requests.append(now)
                return True
            return False
    
    def acquire(self, timeout: float = None) -> bool:
        """
        执行操作（阻塞）
        
        Args:
            timeout: 超时秒数
            
        Returns:
            是否成功执行
        """
        start_time = time.time()
        
        while True:
            if self.try_acquire():
                return True
            
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            time.sleep(0.01)
    
    @property
    def current_count(self) -> int:
        """当前窗口内的请求数"""
        with self._lock:
            now = time.time()
            cutoff = now - self._window_size
            return sum(1 for t in self._requests if t > cutoff)
    
    @property
    def remaining(self) -> int:
        """剩余可用请求数"""
        return max(0, self._max_requests - self.current_count)


class RateLimiter:
    """
    通用限流器
    
    结合令牌桶和滑动窗口的优点。
    """
    
    def __init__(
        self,
        rate: float,
        capacity: int,
        max_burst: int = None,
    ):
        """
        Args:
            rate: 每秒处理数
            capacity: 容量
            max_burst: 最大突发（默认为capacity）
        """
        self._bucket = TokenBucket(rate, max_burst or capacity)
        self._capacity = capacity
    
    def try_acquire(self) -> bool:
        """尝试获取"""
        return self._bucket.try_acquire(1)
    
    def acquire(self, timeout: float = None) -> bool:
        """获取（阻塞）"""
        return self._bucket.acquire(1, timeout)
    
    @property
    def available(self) -> float:
        """可用资源数"""
        return self._bucket.available_tokens


# 全局限流器
_global_limiters: dict = {}


def get_limiter(name: str, rate: float, capacity: int) -> RateLimiter:
    """
    获取或创建限流器
    
    Args:
        name: 限流器名称
        rate: 速率
        capacity: 容量
        
    Returns:
        限流器
    """
    if name not in _global_limiters:
        _global_limiters[name] = RateLimiter(rate, capacity)
    return _global_limiters[name]


# 导出
__all__ = [
    "TokenBucket",
    "SlidingWindow",
    "RateLimiter",
    "get_limiter",
]
