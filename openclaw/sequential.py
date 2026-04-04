"""
Sequential - 顺序执行工具
基于 Claude Code sequential.ts 设计

确保异步操作按顺序执行。
"""
import asyncio
from typing import Callable, TypeVar
from functools import wraps

T = TypeVar('T')


class SequentialExecutor:
    """
    顺序执行器
    
    确保任务按顺序执行，而不是并发。
    """
    
    def __init__(self):
        self._lock = asyncio.Lock()
        self._current_task = None
    
    async def run(self, coro: Callable) -> any:
        """
        顺序执行协程
        
        Args:
            coro: 协程函数
            
        Returns:
            协程结果
        """
        async with self._lock:
            return await coro()


# 全局执行器
_global_executor = SequentialExecutor()


def sequential(coro_func: Callable) -> Callable:
    """
    顺序执行装饰器
    
    确保装饰的async函数按顺序执行。
    
    Args:
        coro_func: async函数
        
    Returns:
        包装后的函数
    """
    @wraps(coro_func)
    async def wrapper(*args, **kwargs):
        async with _global_executor._lock:
            return await coro_func(*args, **kwargs)
    
    return wrapper


def create_sequential_executor() -> SequentialExecutor:
    """
    创建新的顺序执行器
    
    Returns:
        新的执行器
    """
    return SequentialExecutor()


# 导出
__all__ = [
    "SequentialExecutor",
    "sequential",
    "create_sequential_executor",
]
