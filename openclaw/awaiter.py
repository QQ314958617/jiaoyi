"""
Awaiter - await工具
基于 Claude Code awaiter.ts 设计

异步等待工具。
"""
import asyncio
from typing import Any, Callable, List, Optional


async def await_all(*coros):
    """
    等待所有协程
    
    Args:
        *coros: 协程列表
        
    Returns:
        结果列表
    """
    return await asyncio.gather(*coros)


async def await_first(*coros):
    """
    等待第一个完成的协程
    
    Args:
        *coros: 协程列表
        
    Returns:
        第一个结果
    """
    done, pending = await asyncio.wait(
        [asyncio.create_task(c) for c in coros],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    for task in pending:
        task.cancel()
    
    return done.pop().result()


async def await_timeout(coro, timeout_seconds: float, default: Any = None) -> Any:
    """
    带超时的等待
    
    Args:
        coro: 协程
        timeout_seconds: 超时秒数
        default: 超时默认值
        
    Returns:
        协程结果或默认值
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return default


async def retry_until(
    coro_factory: Callable,
    max_attempts: int = 5,
    delay_seconds: float = 1.0,
    backoff: float = 2.0,
):
    """
    重试直到成功
    
    Args:
        coro_factory: 返回协程的工厂函数
        max_attempts: 最大尝试次数
        delay_seconds: 初始延迟
        backoff: 退避倍数
    """
    delay = delay_seconds
    
    for attempt in range(max_attempts):
        try:
            return await coro_factory()
        except Exception:
            if attempt == max_attempts - 1:
                raise
            
            await asyncio.sleep(delay)
            delay *= backoff


async def sleep(seconds: float) -> None:
    """
    睡眠（异步）
    
    Args:
        seconds: 秒数
    """
    await asyncio.sleep(seconds)


def sync_to_async(func: Callable) -> Callable:
    """
    同步转异步装饰器
    
    Args:
        func: 同步函数
        
    Returns:
        异步版本的函数
    """
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper


def async_to_sync(coro):
    """
    异步转同步
    
    Args:
        coro: 协程
        
    Returns:
        同步结果
    """
    loop = asyncio.get_event_loop()
    
    if loop.is_running():
        # 如果事件循环正在运行，创建新循环
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)


class Awaitable:
    """
    可等待对象封装
    """
    
    def __init__(self, coro):
        self._coro = coro
        self._task: Optional[asyncio.Task] = None
    
    def __await__(self):
        return self._coro.__await__()
    
    def start(self) -> None:
        """开始执行"""
        if self._task is None:
            self._task = asyncio.create_task(self._coro)
    
    def cancel(self) -> None:
        """取消"""
        if self._task:
            self._task.cancel()


# 导出
__all__ = [
    "await_all",
    "await_first",
    "await_timeout",
    "retry_until",
    "sleep",
    "sync_to_async",
    "async_to_sync",
    "Awaitable",
]
