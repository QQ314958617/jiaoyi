"""
Backoff - 退避策略
基于 Claude Code backoff.ts 设计

指数退避和抖动。
"""
import asyncio
import random
import time
from typing import Optional


class Backoff:
    """
    退避策略
    
    支持指数退避和抖动。
    """
    
    def __init__(
        self,
        initial_delay_ms: int = 1000,
        max_delay_ms: int = 30000,
        multiplier: float = 2.0,
        jitter: bool = True,
    ):
        """
        Args:
            initial_delay_ms: 初始延迟
            max_delay_ms: 最大延迟
            multiplier: 退避倍数
            jitter: 是否添加抖动
        """
        self._initial_delay_ms = initial_delay_ms
        self._max_delay_ms = max_delay_ms
        self._multiplier = multiplier
        self._jitter = jitter
        
        self._attempt = 0
        self._last_delay_ms: Optional[int] = None
    
    def get_delay(self) -> float:
        """
        获取下次延迟（秒）
        
        Returns:
            延迟秒数
        """
        delay_ms = min(
            self._initial_delay_ms * (self._multiplier ** self._attempt),
            self._max_delay_ms
        )
        
        if self._jitter:
            # 随机抖动 [0.5, 1.0] * delay
            delay_ms *= (0.5 + random.random() * 0.5)
        
        self._last_delay_ms = int(delay_ms)
        return delay_ms / 1000
    
    def record_failure(self) -> None:
        """记录失败，下次延迟更长"""
        self._attempt += 1
    
    def record_success(self) -> None:
        """记录成功，重置"""
        self._attempt = 0
    
    def reset(self) -> None:
        """重置"""
        self._attempt = 0
        self._last_delay_ms = None
    
    @property
    def attempt(self) -> int:
        """当前尝试次数"""
        return self._attempt
    
    @property
    def last_delay_ms(self) -> Optional[int]:
        """上次延迟（毫秒）"""
        return self._last_delay_ms


async def with_backoff(
    func,
    initial_delay_ms: int = 1000,
    max_delay_ms: int = 30000,
    max_attempts: int = 5,
    multiplier: float = 2.0,
    jitter: bool = True,
) -> any:
    """
    带退避的重试
    
    Args:
        func: 要执行的函数（同步）
        initial_delay_ms: 初始延迟
        max_delay_ms: 最大延迟
        max_attempts: 最大尝试次数
        multiplier: 退避倍数
        jitter: 是否抖动
        
    Returns:
        函数结果
    """
    backoff = Backoff(
        initial_delay_ms=initial_delay_ms,
        max_delay_ms=max_delay_ms,
        multiplier=multiplier,
        jitter=jitter,
    )
    
    for attempt in range(max_attempts):
        try:
            result = func()
            return result
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            backoff.record_failure()
            delay = backoff.get_delay()
            await asyncio.sleep(delay)


async def with_backoff_async(
    func,
    initial_delay_ms: int = 1000,
    max_delay_ms: int = 30000,
    max_attempts: int = 5,
    multiplier: float = 2.0,
    jitter: bool = True,
) -> any:
    """
    带退避的重试（异步版本）
    
    Args:
        func: 要执行的异步函数
        initial_delay_ms: 初始延迟
        max_delay_ms: 最大延迟
        max_attempts: 最大尝试次数
        multiplier: 退避倍数
        jitter: 是否抖动
        
    Returns:
        函数结果
    """
    backoff = Backoff(
        initial_delay_ms=initial_delay_ms,
        max_delay_ms=max_delay_ms,
        multiplier=multiplier,
        jitter=jitter,
    )
    
    for attempt in range(max_attempts):
        try:
            result = await func()
            return result
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            backoff.record_failure()
            delay = backoff.get_delay()
            await asyncio.sleep(delay)


# 导出
__all__ = [
    "Backoff",
    "with_backoff",
    "with_backoff_async",
]
