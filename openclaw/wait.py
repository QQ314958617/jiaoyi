"""
Wait - 等待
基于 Claude Code wait.ts 设计

等待工具。
"""
import asyncio
import time
from typing import Callable


def wait_for(condition: Callable[[], bool], timeout: float = None, interval: float = 0.1) -> bool:
    """
    同步等待条件满足
    
    Args:
        condition: 条件函数
        timeout: 超时（秒）
        interval: 检查间隔
        
    Returns:
        是否在超时前满足
    """
    start = time.time()
    
    while True:
        if condition():
            return True
        
        if timeout and (time.time() - start) >= timeout:
            return False
        
        time.sleep(interval)


async def async_wait_for(condition: Callable[[], bool], timeout: float = None, interval: float = 0.1) -> bool:
    """
    异步等待条件满足
    
    Args:
        condition: 条件函数
        timeout: 超时（秒）
        interval: 检查间隔
        
    Returns:
        是否在超时前满足
    """
    start = time.time()
    
    while True:
        if condition():
            return True
        
        if timeout and (time.time() - start) >= timeout:
            return False
        
        await asyncio.sleep(interval)


def wait_until(fn: Callable, target: Callable[[any], bool], timeout: float = None, interval: float = 0.1) -> bool:
    """
    等待函数返回目标值
    
    Args:
        fn: 要执行的函数
        target: 目标值判断
        timeout: 超时
        interval: 检查间隔
        
    Returns:
        是否成功
    """
    start = time.time()
    
    while True:
        result = fn()
        if target(result):
            return True
        
        if timeout and (time.time() - start) >= timeout:
            return False
        
        time.sleep(interval)


async def async_wait_until(fn: Callable, target: Callable[[any], bool], timeout: float = None, interval: float = 0.1) -> bool:
    """
    异步等待函数返回目标值
    """
    start = time.time()
    
    while True:
        result = fn()
        if target(result):
            return True
        
        if timeout and (time.time() - start) >= timeout:
            return False
        
        await asyncio.sleep(interval)


def wait_retry(fn: Callable, max_attempts: int = 3, delay: float = 1.0) -> any:
    """
    等待重试
    
    Args:
        fn: 函数
        max_attempts: 最大尝试次数
        delay: 重试延迟
        
    Returns:
        函数结果
        
    Raises:
        最后一次异常
    """
    last_error = None
    
    for i in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if i < max_attempts - 1:
                time.sleep(delay)
    
    raise last_error


# 导出
__all__ = [
    "wait_for",
    "async_wait_for",
    "wait_until",
    "async_wait_until",
    "wait_retry",
]
