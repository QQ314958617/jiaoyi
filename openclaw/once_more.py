"""
OnceMore - 确保执行一次
基于 Claude Code onceMore.ts 设计

确保操作至少执行一次（用于重试场景）。
"""
import asyncio
from typing import Callable, TypeVar

T = TypeVar('T')


class OnceMore:
    """
    确保至少执行一次
    
    用于需要确保操作至少执行一次的情况（如重试）。
    """
    
    def __init__(self):
        self._executed = False
        self._lock = asyncio.Lock()
    
    async def run(self, fn: Callable) -> T:
        """
        执行函数
        
        Args:
            fn: 要执行的异步函数
            
        Returns:
            函数结果
        """
        async with self._lock:
            if not self._executed:
                self._executed = True
                return await fn()
            return None
    
    @property
    def has_executed(self) -> bool:
        """是否已执行"""
        return self._executed
    
    def reset(self) -> None:
        """重置状态"""
        self._executed = False


async def ensure_at_least_once(
    fn: Callable,
    max_attempts: int = 3,
) -> T:
    """
    确保至少执行一次
    
    Args:
        fn: 要执行的异步函数
        max_attempts: 最大尝试次数
        
    Returns:
        函数结果
    """
    last_error = None
    
    for attempt in range(max_attempts):
        try:
            return await fn()
        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(0.1 * (attempt + 1))
    
    raise last_error


# 导出
__all__ = [
    "OnceMore",
    "ensure_at_least_once",
]
