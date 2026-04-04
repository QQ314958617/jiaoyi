"""
CircuitBreaker - 断路器
基于 Claude Code circuitBreaker.ts 设计

熔断器模式实现。
"""
import time
from enum import Enum
from typing import Callable, TypeVar

T = TypeVar('T')


class CircuitState(Enum):
    """断路器状态"""
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 熔断
    HALF_OPEN = "half_open"  # 半开


class CircuitBreaker:
    """
    断路器
    
    防止级联故障。
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_attempts: int = 3,
    ):
        """
        Args:
            failure_threshold: 触发熔断的失败次数
            recovery_timeout: 尝试恢复的间隔（秒）
            half_open_attempts: 半开状态允许的尝试次数
        """
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_attempts = half_open_attempts
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0
        self._half_open_attempt_count = 0
    
    @property
    def state(self) -> CircuitState:
        """获取当前状态"""
        self._check_state_transition()
        return self._state
    
    def _check_state_transition(self) -> None:
        """检查状态转换"""
        if self._state == CircuitState.OPEN:
            # 检查是否应该转换到HALF_OPEN
            if time.time() - self._last_failure_time >= self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_attempt_count = 0
    
    def record_success(self) -> None:
        """记录成功"""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._half_open_attempts:
                # 恢复
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._success_count = 0
        elif self._state == CircuitState.CLOSED:
            self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self) -> None:
        """记录失败"""
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            # 直接熔断
            self._state = CircuitState.OPEN
            self._half_open_attempt_count = 0
        elif self._state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self._failure_threshold:
                self._state = CircuitState.OPEN
    
    def is_available(self) -> bool:
        """是否可用"""
        self._check_state_transition()
        return self._state != CircuitState.OPEN
    
    def call(self, func: Callable[[], T], *args, **kwargs) -> T:
        """
        执行函数（带断路保护）
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
            
        Returns:
            函数结果
            
        Raises:
            CircuitBreakerOpenError: 断路器打开时
        """
        if not self.is_available():
            raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
    
    async def call_async(self, coro):
        """异步版本"""
        if not self.is_available():
            raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            import asyncio
            result = await coro
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise


class CircuitBreakerOpenError(Exception):
    """断路器打开错误"""
    pass


# 导出
__all__ = [
    "CircuitState",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
]
