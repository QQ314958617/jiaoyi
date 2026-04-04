"""
CircuitBreaker - 断路器
基于 Claude Code circuit.ts 设计

断路器工具。
"""
import time
from enum import Enum


class State(Enum):
    """断路器状态"""
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 断开
    HALF_OPEN = "half_open"  # 半开


class CircuitBreaker:
    """
    断路器
    
    熔断保护，防止级联故障。
    """
    
    def __init__(self, failure_threshold: int = 5, 
                 recovery_timeout: float = 60.0,
                 expected_exception: type = Exception):
        """
        Args:
            failure_threshold: 失败次数阈值
            recovery_timeout: 恢复超时（秒）
            expected_exception: 预期的异常类型
        """
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time = None
        self._state = State.CLOSED
    
    @property
    def state(self) -> State:
        """当前状态"""
        if self._state == State.OPEN:
            # 检查是否超时
            if (time.time() - self._last_failure_time) > self._recovery_timeout:
                self._state = State.HALF_OPEN
        return self._state
    
    def call(self, fn: callable, *args, **kwargs):
        """
        调用函数，受断路器保护
        """
        if self.state == State.OPEN:
            raise Exception("Circuit breaker is OPEN")
        
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except self._expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """成功处理"""
        if self._state == State.HALF_OPEN:
            self._state = State.CLOSED
        self._failure_count = 0
    
    def _on_failure(self):
        """失败处理"""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self._failure_threshold:
            self._state = State.OPEN
    
    def reset(self):
        """重置断路器"""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = State.CLOSED


# 导出
__all__ = [
    "State",
    "CircuitBreaker",
]
