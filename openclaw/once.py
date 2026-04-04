"""
Once - 单次执行
基于 Claude Code once.ts 设计

确保函数只执行一次。
"""
from typing import Any, Callable, Optional


def once(fn: Callable) -> Callable:
    """
    确保函数只执行一次
    
    Args:
        fn: 要包装的函数
        
    Returns:
        只执行一次的函数
    """
    _called = [False]
    _result = [None]
    
    def wrapper(*args, **kwargs):
        if not _called[0]:
            _called[0] = True
            _result[0] = fn(*args, **kwargs)
        return _result[0]
    
    wrapper.called = lambda: _called[0]
    return wrapper


class Once:
    """
    单次执行封装
    """
    
    def __init__(self):
        self._called = False
        self._result = None
    
    def call(self, fn: Callable, *args, **kwargs) -> Any:
        """
        执行函数
        
        Args:
            fn: 函数
            *args, **kwargs: 函数参数
            
        Returns:
            函数结果
        """
        if not self._called:
            self._called = True
            self._result = fn(*args, **kwargs)
        return self._result
    
    @property
    def result(self) -> Any:
        """获取结果"""
        return self._result
    
    @property
    def called(self) -> bool:
        """是否已调用"""
        return self._called
    
    def reset(self) -> None:
        """重置"""
        self._called = False
        self._result = None


def after(times: int, fn: Callable) -> Callable:
    """
    函数执行指定次数后触发
    
    Args:
        times: 执行次数
        fn: 要包装的函数
        
    Returns:
        包装后的函数
    """
    _counter = [0]
    
    def wrapper(*args, **kwargs):
        _counter[0] += 1
        if _counter[0] >= times:
            return fn(*args, **kwargs)
        return None
    
    wrapper.calls = lambda: _counter[0]
    return wrapper


def throttle(fn: Callable, interval: float) -> Callable:
    """
    节流函数
    
    Args:
        fn: 要包装的函数
        interval: 最小执行间隔(秒)
        
    Returns:
        节流后的函数
    """
    import time
    _last_call = [0.0]
    
    def wrapper(*args, **kwargs):
        now = time.time()
        if now - _last_call[0] >= interval:
            _last_call[0] = now
            return fn(*args, **kwargs)
        return None
    
    wrapper.last_call = lambda: _last_call[0]
    return wrapper


# 导出
__all__ = [
    "once",
    "Once",
    "after",
    "throttle",
]
