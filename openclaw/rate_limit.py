"""
OpenClaw Rate Limiter
===================
Inspired by Claude Code's retry/async patterns.

限流器，支持：
1. 令牌桶算法
2. 滑动窗口
3. 固定窗口
4. API 限流自动重试
"""

from __future__ import annotations

import asyncio, time, threading
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

# ============================================================================
# 异常
# ============================================================================

class RateLimitError(Exception):
    """限流异常"""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after

# ============================================================================
# 令牌桶限流器
# ============================================================================

class TokenBucket:
    """
    令牌桶算法限流器
    
    特性：
    - 桶容量：最大突发流量
    - 补充速率：每秒补充的令牌数
    - 线程安全
    
    用法：
    ```python
    limiter = TokenBucket(capacity=10, refill_rate=5)  # 最多10个请求，每秒补充5个
    
    for i in range(20):
        if limiter.try_acquire():
            make_request()
        else:
            wait()
    ```
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: 桶容量（最大令牌数）
            refill_rate: 每秒补充的令牌数
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()
    
    def _refill(self) -> None:
        """补充令牌"""
        now = time.monotonic()
        elapsed = now - self._last_refill
        
        # 计算应该补充的令牌数
        new_tokens = elapsed * self.refill_rate
        self._tokens = min(self.capacity, self._tokens + new_tokens)
        self._last_refill = now
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """
        尝试获取令牌
        
        Returns: True if successful, False if rate limited
        """
        with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
    
    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        获取令牌（阻塞等待）
        
        Args:
            tokens: 需要获取的令牌数
            timeout: 最大等待时间（秒），None 表示无限等待
        
        Returns: True if successful, False if timeout
        """
        start = time.monotonic()
        
        while True:
            if self.try_acquire(tokens):
                return True
            
            # 计算需要等待的时间
            wait_time = (tokens - self._tokens) / self.refill_rate
            wait_time = max(0.01, min(wait_time, 0.1))  # 最多等100ms
            
            if timeout is not None:
                elapsed = time.monotonic() - start
                if elapsed + wait_time > timeout:
                    return False
            
            time.sleep(wait_time)
    
    def wait_time(self, tokens: int = 1) -> float:
        """计算需要等待多久才能获取指定令牌数"""
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                return 0
            return (tokens - self._tokens) / self.refill_rate
    
    @property
    def available_tokens(self) -> float:
        """当前可用令牌数"""
        with self._lock:
            self._refill()
            return self._tokens

# ============================================================================
# 滑动窗口限流器
# ============================================================================

class SlidingWindow:
    """
    滑动窗口算法限流器
    
    特性：
    - 窗口大小：时间窗口
    - 最大请求数：窗口内允许的最大请求数
    - 精确限流
    
    用法：
    ```python
    limiter = SlidingWindow(window_seconds=60, max_requests=100)  # 60秒内最多100个请求
    
    for i in range(200):
        if limiter.try_acquire():
            make_request()
        else:
            wait()
    ```
    """
    
    def __init__(self, window_seconds: float, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._requests: deque = deque()
        self._lock = threading.Lock()
    
    def _clean_old(self) -> None:
        """清理过期的请求记录"""
        cutoff = time.monotonic() - self.window_seconds
        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()
    
    def try_acquire(self) -> bool:
        """尝试记录请求"""
        with self._lock:
            self._clean_old()
            
            if len(self._requests) < self.max_requests:
                self._requests.append(time.monotonic())
                return True
            return False
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """获取许可（阻塞等待）"""
        start = time.monotonic()
        
        while True:
            if self.try_acquire():
                return True
            
            if timeout is not None:
                elapsed = time.monotonic() - start
                if elapsed >= timeout:
                    return False
            
            time.sleep(0.01)
    
    def reset(self) -> None:
        """重置"""
        with self._lock:
            self._requests.clear()
    
    @property
    def current_count(self) -> int:
        """当前窗口内的请求数"""
        with self._lock:
            self._clean_old()
            return len(self._requests)
    
    @property
    def retry_after(self) -> float:
        """距离下次可请求的时间（秒）"""
        with self._lock:
            self._clean_old()
            if len(self._requests) < self.max_requests:
                return 0
            
            oldest = self._requests[0]
            return max(0, oldest + self.window_seconds - time.monotonic())

# ============================================================================
# 固定窗口限流器
# ============================================================================

class FixedWindow:
    """
    固定窗口算法限流器
    
    简单实现，适合单实例限流
    """
    
    def __init__(self, window_seconds: float, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._count = 0
        self._window_start = 0
        self._lock = threading.Lock()
    
    def _ensure_window(self) -> None:
        """确保在当前窗口内"""
        now = time.monotonic()
        if now - self._window_start >= self.window_seconds:
            self._count = 0
            self._window_start = now
    
    def try_acquire(self) -> bool:
        """尝试记录请求"""
        with self._lock:
            self._ensure_window()
            
            if self._count < self.max_requests:
                self._count += 1
                return True
            return False
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """获取许可（阻塞等待）"""
        start = time.monotonic()
        
        while True:
            if self.try_acquire():
                return True
            
            if timeout is not None:
                elapsed = time.monotonic() - start
                if elapsed >= timeout:
                    return False
            
            time.sleep(0.01)

# ============================================================================
# API 限流装饰器
# ============================================================================

def rate_limit(max_calls: int, period: float):
    """
    API 限流装饰器
    
    用法：
    ```python
    @rate_limit(10, 1.0)  # 每秒最多10次调用
    async def call_api():
        return await api.request()
    ```
    """
    limiter = SlidingWindow(window_seconds=period, max_requests=max_calls)
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            limiter.acquire()
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# ============================================================================
# 带重试的 API 调用
# ============================================================================

class RateLimitedAPI:
    """
    带限流和重试的 API 调用器
    
    用法：
    ```python
    api = RateLimitedAPI(
        rate_limit=10,      # 每秒10次
        max_retries=3,     # 最多重试3次
        backoff=2.0        # 指数退避
    )
    
    result = await api.call(lambda: requests.get(url))
    ```
    """
    
    def __init__(self, rate_limit: int, period: float = 1.0,
                 max_retries: int = 3, backoff: float = 2.0,
                 initial_delay: float = 0.1):
        self.limiter = SlidingWindow(window_seconds=period, max_requests=rate_limit)
        self.max_retries = max_retries
        self.backoff = backoff
        self.initial_delay = initial_delay
    
    async def call(self, func, *args, **kwargs):
        """执行 API 调用，自动限流和重试"""
        delay = self.initial_delay
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # 等待限流
                self.limiter.acquire(timeout=5.0)
                
                # 执行调用
                result = func(*args, **kwargs)
                
                # 如果是协程，等待完成
                if asyncio.iscoroutine(result):
                    result = await result
                
                return result
                
            except RateLimitError as e:
                last_error = e
                wait_time = e.retry_after or delay
                await asyncio.sleep(wait_time)
                delay *= self.backoff
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= self.backoff
                else:
                    raise
        
        raise last_error

# ============================================================================
# 并发限制器
# ============================================================================

class ConcurrencyLimiter:
    """
    并发数限制器
    
    用法：
    ```python
    limiter = ConcurrencyLimiter(max_concurrent=5)
    
    async with limiter:
        await do_something()
    ```
    """
    
    def __init__(self, max_concurrent: int):
        self.max_concurrent = max_concurrent
        self._current = 0
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
    
    def try_acquire(self) -> bool:
        """尝试获取许可"""
        with self._lock:
            if self._current < self.max_concurrent:
                self._current += 1
                return True
            return False
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """获取许可（阻塞）"""
        with self._lock:
            end_time = time.monotonic() + timeout if timeout else None
            
            while self._current >= self.max_concurrent:
                if end_time:
                    remaining = end_time - time.monotonic()
                    if remaining <= 0:
                        return False
                    self._condition.wait(timeout=remaining)
                else:
                    self._condition.wait()
            
            self._current += 1
            return True
    
    def release(self) -> None:
        """释放许可"""
        with self._lock:
            self._current = max(0, self._current - 1)
            self._condition.notify()
    
    async def __aenter__(self):
        self.acquire()
        return self
    
    async def __aexit__(self, *args):
        self.release()
