"""
Bucket2 - 桶
基于 Claude Code bucket.ts 设计

限流桶工具。
"""
import time
from typing import Optional


class TokenBucket:
    """
    令牌桶
    
    限流算法实现。
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
    
    def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self._last_refill
        tokens_to_add = elapsed * self._refill_rate
        
        self._tokens = min(self._capacity, self._tokens + tokens_to_add)
        self._last_refill = now
    
    def try_consume(self, tokens: int = 1) -> bool:
        """
        尝试消费令牌
        
        Args:
            tokens: 要消费的令牌数
            
        Returns:
            是否成功
        """
        self._refill()
        
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False
    
    def consume(self, tokens: int = 1, blocking: bool = False) -> bool:
        """
        消费令牌
        
        Args:
            tokens: 要消费的令牌数
            blocking: 是否阻塞等待
            
        Returns:
            是否成功
        """
        if blocking:
            while self._tokens < tokens:
                time.sleep(0.01)
                self._refill()
        
        return self.try_consume(tokens)
    
    @property
    def available_tokens(self) -> float:
        """可用令牌数"""
        self._refill()
        return self._tokens


class LeakyBucket:
    """
    漏桶
    
    漏桶算法实现。
    """
    
    def __init__(self, capacity: int, leak_rate: float):
        """
        Args:
            capacity: 桶容量
            leak_rate: 每秒漏出的数量
        """
        self._capacity = capacity
        self._leak_rate = leak_rate
        self._level = 0
        self._last_leak = time.time()
    
    def _leak(self) -> None:
        """漏水"""
        now = time.time()
        elapsed = now - self._last_leak
        leaked = elapsed * self._leak_rate
        
        self._level = max(0, self._level - leaked)
        self._last_leak = now
    
    def try_add(self, amount: int = 1) -> bool:
        """
        尝试添加
        
        Args:
            amount: 添加数量
            
        Returns:
            是否成功
        """
        self._leak()
        
        if self._level + amount <= self._capacity:
            self._level += amount
            return True
        return False
    
    @property
    def level(self) -> float:
        """当前液位"""
        self._leak()
        return self._level


class SlidingWindow:
    """
    滑动窗口
    
    滑动窗口限流算法。
    """
    
    def __init__(self, max_requests: int, window_size: float):
        """
        Args:
            max_requests: 窗口内最大请求数
            window_size: 窗口大小（秒）
        """
        self._max_requests = max_requests
        self._window_size = window_size
        self._requests: list = []
    
    def try_acquire(self) -> bool:
        """
        尝试获取
        
        Returns:
            是否成功
        """
        now = time.time()
        
        # 清理过期的请求
        self._requests = [
            t for t in self._requests
            if now - t < self._window_size
        ]
        
        if len(self._requests) < self._max_requests:
            self._requests.append(now)
            return True
        
        return False


# 导出
__all__ = [
    "TokenBucket",
    "LeakyBucket",
    "SlidingWindow",
]
