"""
Breaker2 - 断路器
基于 Claude Code breaker.ts 设计

断路器工具。
"""
import time
from enum import Enum
from typing import Callable


class State(Enum):
    """断路器状态"""
    CLOSED = "closed"      # 关闭，正常工作
    OPEN = "open"          # 打开，失败快速返回
    HALF_OPEN = "half_open"  # 半开，试探恢复


class CircuitBreaker:
    """
    断路器
    
    防止级联故障。
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30,
        half_open_max_calls: int = 3
    ):
        """
        Args:
            failure_threshold: 失败次数阈值
            recovery_timeout: 恢复超时（秒）
            half_open_max_calls: 半开状态最大尝试次数
        """
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max_calls = half_open_max_calls
        
        self._state = State.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = None
        self._half_open_calls = 0
    
    @property
    def state(self) -> State:
        """当前状态"""
        if self._state == State.OPEN:
            if self._should_attempt_reset():
                self._state = State.HALF_OPEN
                self._half_open_calls = 0
        return self._state
    
    def _should_attempt_reset(self) -> bool:
        """是否应该尝试恢复"""
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self._recovery_timeout
    
    def call(self, fn: Callable, *args, **kwargs):
        """
        调用函数
        
        Args:
            fn: 要执行的函数
            *args, **kwargs: 函数参数
            
        Returns:
            函数结果
            
        Raises:
            CircuitOpenError: 断路器打开
        """
        if self.state == State.OPEN:
            raise CircuitOpenError("Circuit breaker is OPEN")
        
        if self.state == State.HALF_OPEN:
            if self._half_open_calls >= self._half_open_max_calls:
                raise CircuitOpenError("Circuit breaker is HALF_OPEN, max calls reached")
            self._half_open_calls += 1
        
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """成功处理"""
        if self._state == State.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._half_open_max_calls:
                self._state = State.CLOSED
                self._failure_count = 0
                self._success_count = 0
        else:
            self._failure_count = 0
    
    def _on_failure(self) -> None:
        """失败处理"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == State.HALF_OPEN:
            self._state = State.OPEN
        elif self._failure_count >= self._failure_threshold:
            self._state = State.OPEN
    
    def reset(self) -> None:
        """重置断路器"""
        self._state = State.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0
    
    @property
    def failure_count(self) -> int:
        return self._failure_count
    
    @property
    def is_closed(self) -> bool:
        return self._state == State.CLOSED
    
    @property
    def is_open(self) -> bool:
        return self._state == State.OPEN
    
    @property
    def is_half_open(self) -> bool:
        return self._state == State.HALF_OPEN


class CircuitOpenError(Exception):
    """断路器打开错误"""
    pass


# 导出
__all__ = [
    "State",
    "CircuitBreaker",
    "CircuitOpenError",
]
