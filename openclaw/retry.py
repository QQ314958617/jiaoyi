"""
OpenClaw Retry + Rate Limiter
==============================
Inspired by Claude Code's retry patterns and rate limiting design.

核心功能：
1. 指数退避重试（exponential backoff）
2. 速率限制（token bucket / sliding window）
3. 熔断器（circuit breaker）
4. 限流装饰器

API 保护策略：
- Rate Limit (429): 自动等待后重试
- Server Error (5xx): 指数退避重试
- Network Error: 快速失败不重试
- 熔断器: 连续失败N次后暂时"断路"
"""

from __future__ import annotations

import asyncio
import random
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set, TypeVar, Awaitable, Type
from functools import wraps
from enum import Enum

T = TypeVar("T")


# ============================================================================
# 异常类型
# ============================================================================

class RetryableError(Exception):
    """可重试的错误"""
    pass


class RateLimitError(RetryableError):
    """速率限制错误（429）"""
    def __init__(self, retry_after: Optional[float] = None):
        self.retry_after = retry_after
        super().__init__(f"Rate limited, retry after {retry_after}s")


class CircuitOpenError(Exception):
    """熔断器打开"""
    pass


# ============================================================================
# 重试配置
# ============================================================================

@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # 初始延迟（秒）
    max_delay: float = 30.0     # 最大延迟（秒）
    backoff_factor: float = 2.0  # 退避因子
    jitter: bool = True          # 添加随机抖动
    jitter_factor: float = 0.3  # 抖动幅度
    retry_on: tuple = (         # 可重试的异常类型
        RetryableError,
        RateLimitError,
        ConnectionError,
        TimeoutError,
        Exception,  # 默认重试所有
    )


# ============================================================================
# 重试装饰器
# ============================================================================

def retry(
    config: Optional[RetryConfig] = None,
    exceptions: tuple = (Exception,),
):
    """
    同步函数重试装饰器。

    用法：
        @retry(max_attempts=3, initial_delay=1.0)
        def fetch_data():
            return requests.get(url)
    """
    if config is None:
        config = RetryConfig(retry_on=exceptions)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            delay = config.initial_delay

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except config.retry_on as e:
                    last_exception = e

                    if attempt == config.max_attempts:
                        raise

                    # 计算延迟
                    actual_delay = delay
                    if config.jitter:
                        jitter_range = delay * config.jitter_factor
                        actual_delay = delay + random.uniform(-jitter_range, jitter_range)
                    actual_delay = min(actual_delay, config.max_delay)

                    time.sleep(actual_delay)
                    delay *= config.backoff_factor

            if last_exception:
                raise last_exception
            raise RuntimeError("Retry loop exited unexpectedly")

        return wrapper
    return decorator


def retry_async(
    config: Optional[RetryConfig] = None,
    exceptions: tuple = (Exception,),
):
    """
    异步函数重试装饰器。

    用法：
        @retry_async(max_attempts=3, initial_delay=1.0)
        async def fetch_data():
            return await http.get(url)
    """
    if config is None:
        config = RetryConfig(retry_on=exceptions)

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            delay = config.initial_delay

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except config.retry_on as e:
                    last_exception = e

                    if attempt == config.max_attempts:
                        raise

                    # Rate limit 错误使用 retry_after 头
                    if isinstance(e, RateLimitError) and e.retry_after:
                        actual_delay = e.retry_after
                    else:
                        actual_delay = delay
                        if config.jitter:
                            jitter_range = delay * config.jitter_factor
                            actual_delay = delay + random.uniform(-jitter_range, jitter_range)
                        actual_delay = min(actual_delay, config.max_delay)
                        delay *= config.backoff_factor

                    await asyncio.sleep(actual_delay)

            if last_exception:
                raise last_exception
            raise RuntimeError("Retry loop exited unexpectedly")

        return wrapper
    return decorator


# ============================================================================
# 速率限制器
# ============================================================================

class TokenBucket:
    """
    Token Bucket 速率限制器。

    原理：
    - 桶里有 N 个 token
    - 每次请求消耗 1 个 token
    - token 以固定速率补充

    适合：API 调用频率限制
    """

    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: 每秒补充的 token 数量
            capacity: 桶的容量
        """
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1, blocking: bool = True) -> bool:
        """
        尝试消耗 token。

        Args:
            tokens: 要消耗的 token 数量
            blocking: 是否阻塞等待

        Returns:
            True 如果成功获取，False 如果失败（非阻塞模式）
        """
        with self._lock:
            self._refill()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            if not blocking:
                return False

            # 计算需要等待多久
            needed = tokens - self._tokens
            wait_time = needed / self.rate

        time.sleep(wait_time)

        with self._lock:
            self._refill()
            self._tokens -= tokens
            return True

    def _refill(self) -> None:
        """补充 token"""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self.capacity,
            self._tokens + elapsed * self.rate
        )
        self._last_refill = now

    @property
    def available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens


class SlidingWindowLimiter:
    """
    滑动窗口速率限制器。

    原理：
    - 记录最近 N 秒内的请求时间戳
    - 如果请求数超过限制，拒绝

    适合：并发连接数限制
    """

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: list[float] = []
        self._lock = threading.Lock()

    def acquire(self, blocking: bool = True) -> bool:
        """
        尝试获取请求许可。

        Returns:
            True 如果成功，False 如果被拒绝
        """
        now = time.monotonic()

        with self._lock:
            # 清理过期请求
            cutoff = now - self.window_seconds
            self._requests = [t for t in self._requests if t > cutoff]

            if len(self._requests) < self.max_requests:
                self._requests.append(now)
                return True

            if not blocking:
                return False

            # 等待最早请求过期
            if self._requests:
                wait_time = self._requests[0] + self.window_seconds - now
                if wait_time > 0:
                    time.sleep(wait_time)
                # 重试
                self._requests = [t for t in self._requests if t > time.monotonic() - self.window_seconds]
                self._requests.append(time.monotonic())
                return True

            return True


# ============================================================================
# 熔断器
# ============================================================================

class CircuitState(Enum):
    CLOSED = "closed"    # 正常
    OPEN = "open"         # 熔断打开
    HALF_OPEN = "half_open"  # 半开（尝试恢复）


@dataclass
class CircuitBreaker:
    """
    熔断器。

    原理：
    - 连续失败 N 次后，打开熔断器
    - 熔断期间快速失败，不发请求
    - 等待一段时间后，半开，尝试一个请求
    - 成功则关闭，失败则继续打开

    适合：保护下游服务，防止雪崩
    """

    failure_threshold: int = 5    # 打开熔断的连续失败次数
    success_threshold: int = 2     # 关闭熔断的连续成功次数
    timeout: float = 30.0          # 熔断持续时间（秒）
    half_open_max_calls: int = 1  # 半开时允许的试探请求数

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _opened_at: float = field(default=0.0, init=False)
    _half_open_calls: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                # 检查是否超时
                if time.time() - self._opened_at >= self.timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
            return self._state

    def record_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def record_failure(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                # 半开失败，重新打开
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
                self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._opened_at = time.time()

    def allow_request(self) -> bool:
        """检查是否允许请求"""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
        else:
            return False


# ============================================================================
# 综合 API 客户端（带重试+限流+熔断）
# ============================================================================

class ResilientClient:
    """
    带韧性的 API 客户端。

    整合：
    - 重试机制
    - 速率限制
    - 熔断器
    - 指数退避

    用法：
        client = ResilientClient(rate=10, capacity=20)  # 10 req/s, 容量20
        result = client.get("https://api.example.com/data")
    """

    def __init__(
        self,
        rate: float = 10.0,
        capacity: int = 20,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        self._limiter = SlidingWindowLimiter(
            max_requests=int(rate * 10),  # 10秒窗口
            window_seconds=10.0,
        )
        self._token_bucket = TokenBucket(rate=rate, capacity=capacity)
        self._retry_config = retry_config or RetryConfig()
        self._circuit_breaker = circuit_breaker or CircuitBreaker()
        self._lock = threading.Lock()

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        json: Optional[Dict] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求（带保护和重试）。
        """
        import urllib.request
        import urllib.error
        import json as json_mod

        # 1. 熔断器检查
        if not self._circuit_breaker.allow_request():
            raise CircuitOpenError("Circuit breaker is OPEN")

        # 2. 速率限制
        self._limiter.acquire(blocking=True)

        last_error: Optional[Exception] = None
        delay = self._retry_config.initial_delay

        for attempt in range(1, self._retry_config.max_attempts + 1):
            try:
                # Token bucket
                self._token_bucket.consume(blocking=True)

                # 发送请求
                data = json_mod.dumps(json).encode() if json else None
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers=headers or {},
                    method=method,
                )

                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    result = json_mod.loads(resp.read().decode())

                # 成功
                self._circuit_breaker.record_success()
                return result

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    # Rate limited
                    retry_after = None
                    if "Retry-After" in e.headers:
                        retry_after = float(e.headers["Retry-After"])
                    elif "retry-after" in e.headers:
                        retry_after = float(e.headers["retry-after"])

                    if retry_after and attempt < self._retry_config.max_attempts:
                        time.sleep(retry_after)
                        continue

                    self._circuit_breaker.record_failure()
                    raise RateLimitError(retry_after)

                elif 500 <= e.code < 600:
                    # Server error - retry
                    last_error = e
                    self._circuit_breaker.record_failure()

                    if attempt == self._retry_config.max_attempts:
                        raise

                    actual_delay = delay
                    if self._retry_config.jitter:
                        actual_delay = delay + random.uniform(
                            -delay * self._retry_config.jitter_factor,
                            delay * self._retry_config.jitter_factor
                        )
                    actual_delay = min(actual_delay, self._retry_config.max_delay)
                    time.sleep(actual_delay)
                    delay *= self._retry_config.backoff_factor

                else:
                    # Client error (4xx except 429) - don't retry
                    self._circuit_breaker.record_failure()
                    raise

            except urllib.error.URLError as e:
                # Network error
                last_error = e
                self._circuit_breaker.record_failure()

                if attempt < self._retry_config.max_attempts:
                    actual_delay = delay
                    if self._retry_config.jitter:
                        actual_delay = delay + random.uniform(-delay * 0.3, delay * 0.3)
                    time.sleep(min(actual_delay, self._retry_config.max_delay))
                    delay *= self._retry_config.backoff_factor
                else:
                    raise

        if last_error:
            raise last_error
        raise RuntimeError("Request loop exited unexpectedly")

    def get(self, url: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
        return self.request("GET", url, headers=headers)

    def post(self, url: str, json: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        return self.request("POST", url, json=json, headers=headers)


# ============================================================================
# 全局限流器注册表
# ============================================================================

_global_limiters: Dict[str, Any] = {}
_limiter_lock = threading.Lock()


def get_limiter(name: str, rate: float = 10, capacity: int = 20) -> TokenBucket:
    """获取或创建全局限流器"""
    with _limiter_lock:
        if name not in _global_limiters:
            _global_limiters[name] = TokenBucket(rate=rate, capacity=capacity)
        return _global_limiters[name]


def rate_limit(
    name: str,
    rate: float = 10,
    capacity: int = 20,
):
    """
    限流装饰器。

    用法：
        @rate_limit("api_calls", rate=5, capacity=10)
        def call_api():
            return requests.get(url)
    """
    limiter = get_limiter(name, rate, capacity)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            limiter.consume(blocking=True)
            return func(*args, **kwargs)
        return wrapper
    return decorator
