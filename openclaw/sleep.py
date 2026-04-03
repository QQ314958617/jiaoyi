"""
OpenClaw Sleep Utilities
====================
Inspired by Claude Code's src/utils/sleep.ts.

睡眠工具，支持：
1. 可取消的 sleep
2. 带超时的 wait
3. 指数退避
"""

from __future__ import annotations

import asyncio, time
from typing import Optional

# ============================================================================
# 基础睡眠
# ============================================================================

async def sleep(ms: float, signal=None, *, throw_on_abort: bool = False) -> None:
    """
    可取消的睡眠
    
    Args:
        ms: 睡眠毫秒数
        signal: 可选的 AbortSignal
        throw_on_abort: 取消时是否抛出异常
    
    用法：
    ```python
    # 普通睡眠
    await sleep(1000)  # 1秒
    
    # 可取消的睡眠
    await sleep(1000, signal=controller.signal)
    
    # 取消时抛出异常
    await sleep(1000, signal=controller.signal, throw_on_abort=True)
    ```
    """
    loop = asyncio.get_event_loop()
    
    # 检查是否已取消
    if signal is not None and getattr(signal, 'aborted', False):
        if throw_on_abort:
            reason = getattr(signal, 'reason', None) or AbortError("Aborted")
            raise reason
        return
    
    try:
        if signal is not None:
            # 带 AbortSignal 的睡眠
            try:
                # 使用 asyncio.wait_for 实现可取消的睡眠
                await asyncio.wait_for(
                    asyncio.sleep(ms / 1000),
                    timeout=ms / 1000
                )
            except asyncio.TimeoutError:
                # 正常完成
                pass
            
            # 检查是否被取消
            if signal is not None and getattr(signal, 'aborted', False):
                if throw_on_abort:
                    reason = getattr(signal, 'reason', None) or AbortError("Aborted")
                    raise reason
        else:
            # 普通睡眠
            await asyncio.sleep(ms / 1000)
    except asyncio.CancelledError:
        if throw_on_abort:
            raise AbortError("Sleep cancelled")
        raise


class AbortError(Exception):
    """取消异常"""
    pass


def sleep_sync(ms: float) -> None:
    """
    同步睡眠（阻塞）
    
    Args:
        ms: 睡眠毫秒数
    """
    time.sleep(ms / 1000)


# ============================================================================
# 带超时的操作
# ============================================================================

async def with_timeout(coro, ms: float, message: str = "Operation timed out"):
    """
    超时包装器
    
    Args:
        coro: 协程
        ms: 超时毫秒数
        message: 超时错误消息
    
    Returns:
        协程结果
    
    Raises:
        asyncio.TimeoutError: 超时
    
    用法：
    ```python
    result = await with_timeout(fetch_data(), 5000, "数据获取超时")
    ```
    """
    try:
        return await asyncio.wait_for(coro, timeout=ms / 1000)
    except asyncio.TimeoutError:
        raise TimeoutError(message)


def with_timeout_sync(coro, ms: float, message: str = "Operation timed out"):
    """
    同步版本的超时包装器（阻塞等待）
    """
    try:
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(
            asyncio.wait_for(coro, timeout=ms / 1000)
        )
    except asyncio.TimeoutError:
        raise TimeoutError(message)
    finally:
        loop.close()


# ============================================================================
# 指数退避
# ============================================================================

async def exponential_backoff(
    initial_ms: float = 100,
    max_ms: float = 30000,
    factor: float = 2.0,
    jitter: bool = True,
    signal=None,
) -> float:
    """
    指数退避
    
    Args:
        initial_ms: 初始延迟
        max_ms: 最大延迟
        factor: 退避倍数
        jitter: 是否添加随机抖动
        signal: 可选的 AbortSignal
    
    Yields:
        当前应该等待的毫秒数
    
    用法：
    ```python
    delay = initial_ms
    async for delay in exponential_backoff(initial_ms=100):
        try:
            await do_operation()
            break
        except RetryableError:
            print(f"Retrying in {delay}ms")
            await sleep(delay, signal)
            delay = min(delay * factor, max_ms)
    ```
    """
    import random
    
    delay = initial_ms
    
    while True:
        # 添加随机抖动
        if jitter:
            delay = delay * (0.5 + random.random())
        
        yield delay
        
        # 检查是否取消
        if signal is not None and getattr(signal, 'aborted', False):
            break
        
        # 等待
        await sleep(delay)
        
        # 计算下一次延迟
        delay = min(delay * factor, max_ms)


# ============================================================================
# 重试循环
# ============================================================================

async def retry_with_backoff(
    func,
    max_attempts: int = 5,
    initial_ms: float = 100,
    max_ms: float = 30000,
    factor: float = 2.0,
    exceptions: tuple = (Exception,),
    signal=None,
):
    """
    带指数退避的重试
    
    Args:
        func: 要重试的函数（同步或异步）
        max_attempts: 最大尝试次数
        initial_ms: 初始延迟
        max_ms: 最大延迟
        factor: 退避倍数
        exceptions: 需要重试的异常类型
        signal: 可选的 AbortSignal
    
    Returns:
        函数结果
    
    用法：
    ```python
    result = await retry_with_backoff(
        lambda: api.call(),
        max_attempts=3,
        initial_ms=500
    )
    ```
    """
    delay = initial_ms
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            # 支持异步函数
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except exceptions as e:
            last_error = e
            
            if attempt < max_attempts - 1:
                # 等待后再试
                if signal is not None and getattr(signal, 'aborted', False):
                    break
                
                await sleep(delay, signal)
                delay = min(delay * factor, max_ms)
            else:
                raise last_error
    
    raise last_error


# ============================================================================
# 等待条件
# ============================================================================

async def wait_for_condition(
    condition_func,
    timeout_ms: float = 30000,
    interval_ms: float = 100,
    signal=None,
):
    """
    等待条件满足
    
    Args:
        condition_func: 返回 bool 的函数
        timeout_ms: 超时毫秒数
        interval_ms: 检查间隔毫秒数
        signal: 可选的 AbortSignal
    
    Returns:
        True if condition met, False if timeout
    
    用法：
    ```python
    ready = await wait_for_condition(
        lambda: check_queue(),
        timeout_ms=10000,
        interval_ms=500
    )
    ```
    """
    start = time.time()
    timeout = timeout_ms / 1000
    
    while True:
        if condition_func():
            return True
        
        if time.time() - start >= timeout:
            return False
        
        if signal is not None and getattr(signal, 'aborted', False):
            return False
        
        await sleep(interval_ms, signal)
