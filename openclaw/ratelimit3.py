"""
RateLimit3 - 限流3
基于 Claude Code rateLimit3.ts 设计

异步限流实现。
"""
import asyncio
import time
from typing import Dict, Optional


class AsyncTokenBucket:
    """
    异步令牌桶
    
    异步友好的限流器。
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
        self._lock: Optional[asyncio.Lock] = None
    
    async def _get_lock(self) -> asyncio.Lock:
        """获取锁"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """尝试获取"""
        async with await self._get_lock():
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
    
    async def acquire(self, tokens: int = 1, timeout: float = None) -> bool:
        """获取（阻塞）"""
        start = time.time()
        
        while True:
            if await self.try_acquire(tokens):
                return True
            
            if timeout is not None and time.time() - start >= timeout:
                return False
            
            await asyncio.sleep(0.1)
    
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


class AsyncSlidingWindow:
    """
    异步滑动窗口
    """
    
    def __init__(
        self,
        max_requests: int,
        window_ms: int,
    ):
        self._max_requests = max_requests
        self._window_ms = window_ms
        self._requests: list = []
        self._lock: Optional[asyncio.Lock] = None
    
    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    async def try_acquire(self) -> bool:
        """尝试获取"""
        async with await self._get_lock():
            now = time.time()
            window_start = now - self._window_ms / 1000
            
            # 清理过期
            self._requests = [t for t in self._requests if t > window_start]
            
            if len(self._requests) < self._max_requests:
                self._requests.append(now)
                return True
            
            return False
    
    async def acquire(self, timeout: float = None) -> bool:
        """获取（阻塞）"""
        start = time.time()
        
        while True:
            if await self.try_acquire():
                return True
            
            if timeout is not None and time.time() - start >= timeout:
                return False
            
            await asyncio.sleep(0.01)


class AsyncMultiLimiter:
    """
    异步多键限流器
    """
    
    def __init__(self, rate: float, capacity: int):
        self._rate = rate
        self._capacity = capacity
        self._limiters: Dict[str, AsyncTokenBucket] = {}
        self._lock: Optional[asyncio.Lock] = None
    
    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock
    
    async def _get_limiter(self, key: str) -> AsyncTokenBucket:
        """获取键的限流器"""
        async with await self._get_lock():
            if key not in self._limiters:
                self._limiters[key] = AsyncTokenBucket(
                    self._rate, self._capacity
                )
            return self._limiters[key]
    
    async def try_acquire(self, key: str, tokens: int = 1) -> bool:
        """尝试获取"""
        limiter = await self._get_limiter(key)
        return await limiter.try_acquire(tokens)
    
    async def acquire(self, key: str, tokens: int = 1, timeout: float = None) -> bool:
        """获取（阻塞）"""
        limiter = await self._get_limiter(key)
        return await limiter.acquire(tokens, timeout)


# 导出
__all__ = [
    "AsyncTokenBucket",
    "AsyncSlidingWindow",
    "AsyncMultiLimiter",
]
