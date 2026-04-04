"""
Timeout2 - 超时
基于 Claude Code timeout.ts 设计

超时工具。
"""
import asyncio
import time
from typing import Callable, Type


class TimeoutError(Exception):
    """超时错误"""
    pass


def timeout(seconds: float, default: any = None) -> Callable:
    """
    超时装饰器
    
    Args:
        seconds: 超时秒数
        default: 超时默认值
        
    Returns:
        装饰器
    """
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start = time.time()
            result = [None]
            error = [None]
            
            def target():
                try:
                    result[0] = fn(*args, **kwargs)
                except Exception as e:
                    error[0] = e
            
            import threading
            t = threading.Thread(target=target)
            t.start()
            t.join(timeout=seconds)
            
            if t.is_alive():
                return default
            
            if error[0]:
                raise error[0]
            
            return result[0]
        
        return wrapper
    return decorator


def timeout_sync(fn: Callable, seconds: float, default: any = None):
    """
    同步超时
    
    Args:
        fn: 函数
        seconds: 超时秒数
        default: 超时默认值
        
    Returns:
        函数结果或默认值
    """
    start = time.time()
    result = [None]
    error = [None]
    
    def target():
        try:
            result[0] = fn()
        except Exception as e:
            error[0] = e
    
    import threading
    t = threading.Thread(target=target)
    t.start()
    t.join(timeout=seconds)
    
    if t.is_alive():
        return default
    
    if error[0]:
        raise error[0]
    
    return result[0]


async def timeout_async(fn: Callable, seconds: float):
    """
    异步超时
    
    Args:
        fn: 异步函数
        seconds: 超时秒数
        
    Returns:
        函数结果
        
    Raises:
        asyncio.TimeoutError: 超时
    """
    return await asyncio.wait_for(fn(), timeout=seconds)


def with_timeout(seconds: float, fn: Callable, *args, **kwargs):
    """
    带超时的函数执行
    
    Args:
        seconds: 超时秒数
        fn: 函数
        *args, **kwargs: 函数参数
        
    Returns:
        (success, result)
    """
    try:
        result = timeout_sync(lambda: fn(*args, **kwargs), seconds)
        return True, result
    except Exception as e:
        return False, e


# 导出
__all__ = [
    "TimeoutError",
    "timeout",
    "timeout_sync",
    "timeout_async",
    "with_timeout",
]
