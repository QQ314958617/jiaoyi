"""
Timeout - 超时
基于 Claude Code timeout.ts 设计

超时工具。
"""
import time
from typing import Callable


def timeout(fn: Callable, seconds: float, default=None) -> any:
    """
    带超时的函数执行
    
    Args:
        fn: 函数
        seconds: 超时秒数
        default: 超时默认值
        
    Returns:
        函数结果或默认值
    """
    start = time.time()
    result = None
    
    def worker():
        nonlocal result
        result = fn()
    
    import threading
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(seconds)
    
    if thread.is_alive():
        return default
    
    return result


def timeout_ms(fn: Callable, milliseconds: int, default=None) -> any:
    """毫秒超时版本"""
    return timeout(fn, milliseconds / 1000, default)


class TimeoutError(Exception):
    """超时错误"""
    pass


def timeout_or_raise(fn: Callable, seconds: float) -> any:
    """
    超时则抛出异常
    """
    start = time.time()
    result = [None]
    error = [None]
    
    def worker():
        try:
            result[0] = fn()
        except Exception as e:
            error[0] = e
    
    import threading
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(seconds)
    
    if thread.is_alive():
        raise TimeoutError(f"Function timed out after {seconds}s")
    
    if error[0]:
        raise error[0]
    
    return result[0]


# 导出
__all__ = [
    "timeout",
    "timeout_ms",
    "TimeoutError",
    "timeout_or_raise",
]
