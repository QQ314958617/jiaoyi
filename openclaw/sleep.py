"""
Sleep - 延迟
基于 Claude Code sleep.ts 设计

延迟工具。
"""
import asyncio
import time


def sleep(seconds: float) -> None:
    """
    同步延迟
    
    Args:
        seconds: 秒数
    """
    time.sleep(seconds)


def sleep_ms(ms: int) -> None:
    """
    同步延迟（毫秒）
    
    Args:
        ms: 毫秒数
    """
    time.sleep(ms / 1000)


async def async_sleep(seconds: float) -> None:
    """
    异步延迟
    
    Args:
        seconds: 秒数
    """
    await asyncio.sleep(seconds)


async def async_sleep_ms(ms: int) -> None:
    """
    异步延迟（毫秒）
    
    Args:
        ms: 毫秒数
    """
    await asyncio.sleep(ms / 1000)


def wait_for(fn, timeout: float = None, interval: float = 0.1):
    """
    等待条件满足
    
    Args:
        fn: 条件函数 () -> bool
        timeout: 超时（秒）
        interval: 检查间隔
        
    Returns:
        是否成功
    """
    start = time.time()
    
    while True:
        if fn():
            return True
        
        if timeout and (time.time() - start) > timeout:
            return False
        
        time.sleep(interval)


async def async_wait_for(fn, timeout: float = None, interval: float = 0.1):
    """
    异步等待条件满足
    
    Args:
        fn: 条件函数 () -> bool
        timeout: 超时（秒）
        interval: 检查间隔
        
    Returns:
        是否成功
    """
    start = time.time()
    
    while True:
        if fn():
            return True
        
        if timeout and (time.time() - start) > timeout:
            return False
        
        await asyncio.sleep(interval)


# 导出
__all__ = [
    "sleep",
    "sleep_ms",
    "async_sleep",
    "async_sleep_ms",
    "wait_for",
    "async_wait_for",
]
