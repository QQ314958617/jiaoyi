"""
Bucket - 令牌桶
基于 Claude Code bucket.ts 设计

令牌桶算法实现。
"""
import time
from threading import Lock


class TokenBucket:
    """
    令牌桶
    
    漏桶算法的变体。
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: 桶容量
            refill_rate: 每秒补充的令牌数
        """
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = float(capacity)
        self._last_refill = time.time()
        self._lock = Lock()
    
    def try_consume(self, tokens: int = 1) -> bool:
        """
        尝试消费令牌
        
        Args:
            tokens: 要消费的令牌数
            
        Returns:
            是否成功
        """
        with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
    
    def consume(self, tokens: int = 1, timeout: float = None) -> bool:
        """
        消费令牌（阻塞）
        
        Args:
            tokens: 要消费的令牌数
            timeout: 超时秒数
            
        Returns:
            是否成功
        """
        start = time.time()
        
        while True:
            if self.try_consume(tokens):
                return True
            
            if timeout is not None and time.time() - start >= timeout:
                return False
            
            # 等待一点时间再试
            wait_time = (tokens - self._tokens) / self._refill_rate
            time.sleep(min(wait_time, 0.1))
    
    def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self._last_refill
        tokens_to_add = elapsed * self._refill_rate
        
        self._tokens = min(
            self._capacity,
            self._tokens + tokens_to_add
        )
        self._last_refill = now
    
    @property
    def tokens(self) -> float:
        """当前令牌数"""
        with self._lock:
            self._refill()
            return self._tokens


class LeakyBucket:
    """
    漏桶
    
    固定速率输出。
    """
    
    def __init__(self, capacity: int, leak_rate: float):
        """
        Args:
            capacity: 桶容量
            leak_rate: 每秒漏出的速率
        """
        self._capacity = capacity
        self._leak_rate = leak_rate
        self._water = 0.0
        self._last_leak = time.time()
        self._lock = Lock()
    
    def try_add(self, water: float = 1.0) -> bool:
        """
        尝试添加水
        
        Args:
            water: 水量
            
        Returns:
            是否成功（桶未满）
        """
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
        leaked = elapsed * self._leak_rate
        
        self._water = max(0, self._water - leaked)
        self._last_leak = now
    
    @property
    def water(self) -> float:
        """当前水量"""
        with self._lock:
            self._leak()
            return self._water


# 导出
__all__ = [
    "TokenBucket",
    "LeakyBucket",
]
