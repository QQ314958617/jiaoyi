"""
Rate Limit Reset - 限流重置
基于 Claude Code rateLimitReset.ts 设计

限流器状态管理。
"""
import threading
import time
from typing import Dict, Optional


class RateLimitState:
    """限流器状态"""
    
    def __init__(
        self,
        limit: int,
        remaining: int,
        reset_at: float,
    ):
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at
        self.retry_after: Optional[float] = None


class RateLimitStore:
    """
    限流状态存储
    
    存储各限流器的状态。
    """
    
    def __init__(self):
        self._states: Dict[str, RateLimitState] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[RateLimitState]:
        """获取限流状态"""
        with self._lock:
            return self._states.get(key)
    
    def set(self, key: str, state: RateLimitState) -> None:
        """设置限流状态"""
        with self._lock:
            self._states[key] = state
    
    def update(
        self,
        key: str,
        limit: int,
        remaining: int,
        reset_at: float,
        retry_after: float = None,
    ) -> None:
        """
        更新限流状态
        
        Args:
            key: 限流器键
            limit: 限制数
            remaining: 剩余数
            reset_at: 重置时间戳
            retry_after: 重试时间戳
        """
        with self._lock:
            self._states[key] = RateLimitState(
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after,
            )
    
    def decrement(self, key: str) -> None:
        """
        减少剩余次数
        
        Args:
            key: 限流器键
        """
        with self._lock:
            if key in self._states:
                state = self._states[key]
                if state.remaining > 0:
                    state.remaining -= 1
    
    def clear(self, key: str) -> None:
        """清除限流状态"""
        with self._lock:
            if key in self._states:
                del self._states[key]
    
    def clear_all(self) -> None:
        """清除所有限流状态"""
        with self._lock:
            self._states.clear()
    
    def is_rate_limited(self, key: str) -> bool:
        """
        检查是否被限流
        
        Args:
            key: 限流器键
            
        Returns:
            是否被限流
        """
        state = self.get(key)
        if state is None:
            return False
        
        if state.remaining <= 0:
            if time.time() >= state.reset_at:
                return False
            return True
        
        return False
    
    def get_retry_after(self, key: str) -> Optional[float]:
        """
        获取需要等待的时间
        
        Args:
            key: 限流器键
            
        Returns:
            需要等待的秒数，None表示不需要等待
        """
        state = self.get(key)
        if state is None:
            return None
        
        if state.remaining > 0:
            return None
        
        now = time.time()
        if now >= state.reset_at:
            return None
        
        return state.reset_at - now


# 全局限流状态存储
_rate_limit_store: Optional[RateLimitStore] = None


def get_rate_limit_store() -> RateLimitStore:
    """获取全局限流状态存储"""
    global _rate_limit_store
    if _rate_limit_store is None:
        _rate_limit_store = RateLimitStore()
    return _rate_limit_store


# 导出
__all__ = [
    "RateLimitState",
    "RateLimitStore",
    "get_rate_limit_store",
]
