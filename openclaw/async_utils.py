"""
OpenClaw Async Utilities
====================
Inspired by Claude Code's async patterns.

异步工具，支持：
1. debounce（防抖）
2. throttle（节流）
3. timeout（超时控制）
4. retry（重试）
5. 并发限制
"""

from __future__ import annotations

import asyncio, functools, threading, time
from typing import Any, Callable, Coroutine, Optional, TypeVar

T = TypeVar('T')

# ============================================================================
# Debounce（防抖）
# ============================================================================

def debounce(wait_ms: int):
    """
    防抖装饰器
    
    函数被调用后，等待 wait_ms 毫秒后执行。
    如果在等待期间再次调用，则重新计时。
    
    用法：
    ```python
    @debounce(500)
    async def on_input(text):
        await do_something(text)
    ```
    """
    def decorator(func: Callable[..., Coroutine]) -> Callable:
        _timers: dict[str, asyncio.Task] = {}
        _locks: dict[str, asyncio.Lock] = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}"
            lock = _locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                _locks[key] = lock
            
            async with lock:
                # 取消之前的定时器
                if key in _timers:
                    _timers[key].cancel()
                
                # 创建新的定时器
                async def run():
                    await asyncio.sleep(wait_ms / 1000)
                    await func(*args, **kwargs)
                    async with lock:
                        _timers.pop(key, None)
                
                _timers[key] = asyncio.create_task(run())
        
        return wrapper
    return decorator

class Debouncer:
    """
    防抖管理器
    
    用法：
    ```python
    debouncer = Debouncer(wait_ms=500)
    
    def on_input(text):
        debouncer.debounce("key", lambda: do_something(text))
    ```
    """
    
    def __init__(self, wait_ms: int):
        self.wait_ms = wait_ms
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
    
    def debounce(self, key: str, func: Callable) -> None:
        """防抖执行"""
        with self._lock:
            # 取消之前的定时器
            if key in self._timers:
                self._timers[key].cancel()
            
            # 创建新的定时器
            timer = threading.Timer(self.wait_ms / 1000, func)
            self._timers[key] = timer
            timer.start()
    
    def cancel(self, key: str) -> None:
        """取消特定 key 的防抖"""
        with self._lock:
            if key in self._timers:
                self._timers[key].cancel()
                del self._timers[key]
    
    def cancel_all(self) -> None:
        """取消所有防抖"""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()

# ============================================================================
# Throttle（节流）
# ============================================================================

def throttle(wait_ms: int):
    """
    节流装饰器
    
    函数被调用后，等待 wait_ms 毫秒后才能再次执行。
    如果在等待期间调用，则忽略。
    
    用法：
    ```python
    @throttle(1000)
    async def on_click():
        await do_something()
    ```
    """
    def decorator(func: Callable[..., Coroutine]) -> Callable:
        _last_run: dict[str, float] = {}
        _locks: dict[str, asyncio.Lock] = {}
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}"
            lock = _locks.get(key)
            if lock is None:
                lock = asyncio.Lock()
                _locks[key] = lock
            
            async with lock:
                now = time.time()
                last = _last_run.get(key, 0)
                elapsed = (now - last) * 1000
                
                if elapsed >= wait_ms:
                    _last_run[key] = now
                    await func(*args, **kwargs)
        
        return wrapper
    return decorator

class Throttler:
    """
    节流管理器
    """
    
    def __init__(self, wait_ms: int):
        self.wait_ms = wait_ms
        self._last_run: dict[str, float] = {}
        self._lock = threading.Lock()
    
    def throttle(self, key: str, func: Callable) -> bool:
        """
        节流执行
        
        Returns: True if executed, False if throttled
        """
        with self._lock:
            now = time.time()
            last = self._last_run.get(key, 0)
            elapsed = (now - last) * 1000
            
            if elapsed >= self.wait_ms:
                self._last_run[key] = now
                func()
                return True
            return False

# ============================================================================
# Timeout（超时）
# ============================================================================

async def with_timeout(coro: Coroutine, timeout_ms: int, 
                       default: Any = None) -> Any:
    """
    超时控制
    
    用法：
    ```python
    result = await with_timeout(fetch_data(), 5000, default=None)
    ```
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_ms / 1000)
    except asyncio.TimeoutError:
        return default

def timeout_ms(ms: int):
    """
    超时装饰器
    
    用法：
    ```python
    @timeout_ms(5000)
    async def fetch_data():
        return await api.get()
    ```
    """
    def decorator(func: Callable[..., Coroutine]) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await with_timeout(func(*args, **kwargs), ms)
        return wrapper
    return decorator

# ============================================================================
# Retry（重试）
# ============================================================================

async def retry_async(func: Callable[..., Coroutine], 
                     max_attempts: int = 3,
                     delay_ms: int = 1000,
                     backoff: float = 2.0,
                     exceptions: tuple = (Exception,)) -> Any:
    """
    异步重试
    
    Args:
        func: 异步函数
        max_attempts: 最大尝试次数
        delay_ms: 初始延迟（毫秒）
        backoff: 退避倍数
        exceptions: 需要重试的异常类型
    
    用法：
    ```python
    result = await retry_async(
        lambda: api.call(),
        max_attempts=3,
        delay_ms=1000
    )
    ```
    """
    delay = delay_ms / 1000
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_error = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)
                delay *= backoff
    
    raise last_error

def retry(max_attempts: int = 3, delay_ms: int = 1000, 
         backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    同步重试装饰器
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = delay_ms / 1000
            last_error = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                        delay *= backoff
            
            raise last_error
        return wrapper
    return decorator

# ============================================================================
# 并发限制
# ============================================================================

class Semaphore:
    """
    异步信号量（限制并发数）
    """
    
    def __init__(self, max_concurrent: int):
        self._sem = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        await self._sem.acquire()
        return self
    
    async def __aexit__(self, *args):
        self._sem.release()
    
    async def run(self, coro: Coroutine) -> Any:
        """在信号量控制下运行协程"""
        async with self:
            return await coro

class ConcurrencyLimiter:
    """
    并发限制器
    
    用法：
    ```python
    limiter = ConcurrencyLimiter(max_concurrent=5)
    
    async def process(item):
        async with limiter:
            await do_work(item)
    
    # 批量处理
    await asyncio.gather(*[process(item) for item in items])
    ```
    """
    
    def __init__(self, max_concurrent: int = 5):
        self._sem = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        await self._sem.acquire()
        return self
    
    async def __aexit__(self, *args):
        self._sem.release()
    
    async def run(self, coro: Coroutine) -> Any:
        async with self:
            return await coro

# ============================================================================
# 批量处理
# ============================================================================

async def batch_process(items: list, 
                       processor: Callable[[Any], Coroutine],
                       batch_size: int = 10,
                       max_concurrent: int = 5) -> list:
    """
    批量并发处理
    
    Args:
        items: 待处理列表
        processor: 处理函数（异步）
        batch_size: 每批大小
        max_concurrent: 最大并发数
    
    Returns: 处理结果列表
    """
    results = []
    limiter = ConcurrencyLimiter(max_concurrent)
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        
        async def process_batch():
            batch_results = []
            for item in batch:
                async with limiter:
                    result = await processor(item)
                    batch_results.append(result)
            return batch_results
        
        batch_results = await process_batch()
        results.extend(batch_results)
    
    return results
