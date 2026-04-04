"""
Bucket - 令牌桶
基于 Claude Code bucket.ts 设计

令牌桶限流工具。
"""
import time
from threading import Lock


class Bucket:
    """
    令牌桶
    
    用于速率限制。
    """
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: 每秒补充的令牌数
            capacity: 桶容量
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._last_refill = time.time()
        self._lock = Lock()
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self._last_refill
        refill = elapsed * self._rate
        self._tokens = min(self._capacity, self._tokens + refill)
        self._last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        尝试消费令牌
        
        Returns:
            是否成功
        """
        with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
    
    def wait_for(self, tokens: int = 1) -> float:
        """
        等待直到获得令牌
        
        Returns:
            等待秒数
        """
        while True:
            with self._lock:
                self._refill()
                
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return 0.0
            
            # 计算需要等待多久
            needed = tokens - self._tokens
            wait_time = needed / self._rate
            time.sleep(min(wait_time, 0.1))


class RateLimiter:
    """简单速率限制器"""
    
    def __init__(self, rate: float, capacity: int = None):
        """
        Args:
            rate: 每秒请求数
            capacity: 桶容量（默认=rate）
        """
        if capacity is None:
            capacity = int(rate)
        self._bucket = Bucket(rate, capacity)
    
    def allow(self) -> bool:
        """是否允许"""
        return self._bucket.consume()
    
    def wait_for(self):
        """等待许可"""
        self._bucket.wait_for()


# 导出
__all__ = [
    "Bucket",
    "RateLimiter",
]
