"""
Throttle2 - 节流
基于 Claude Code throttle.ts 设计

节流工具。
"""
import time
import threading
from typing import Callable, Optional


def throttle(wait: float, options: dict = None) -> Callable:
    """
    节流装饰器
    
    Args:
        wait: 间隔时间（秒）
        options: { leading: bool, trailing: bool }
        
    Returns:
        装饰器
    """
    opts = {'leading': True, 'trailing': True}
    if options:
        opts.update(options)
    
    last_time = [0.0]
    result = [None]
    timer = [None]
    
    def decorator(fn: Callable) -> Callable:
        def throttled(*args, **kwargs):
            def call():
                return fn(*args, **kwargs)
            
            elapsed = time.time() - last_time[0]
            
            if elapsed >= wait:
                if opts['leading']:
                    result[0] = call()
                    last_time[0] = time.time()
            else:
                if opts['trailing'] and not timer[0]:
                    timer[0] = threading.Timer(wait - elapsed, lambda: (
                        last_time[0].__set__(throttled, time.time()),
                        result[0].__setitem__(0, call()) if isinstance(result[0], list) else None
                    ))
                    timer[0].start()
            
            return result[0]
        
        throttled.cancel = lambda: timer[0] and timer[0].cancel()
        return throttled
    
    return decorator


class Throttler:
    """
    节流器
    """
    
    def __init__(self, wait: float, leading: bool = True, trailing: bool = True):
        """
        Args:
            wait: 间隔时间
            leading: 是否首次立即执行
            trailing: 是否最后一次延迟执行
        """
        self._wait = wait
        self._leading = leading
        self._trailing = trailing
        self._last_time = 0
        self._timer = None
        self._result = None
    
    def __call__(self, fn: Callable, *args, **kwargs):
        """执行"""
        def call():
            return fn(*args, **kwargs)
        
        now = time.time()
        
        if self._last_time == 0 and not self._leading:
            self._last_time = now
        
        elapsed = now - self._last_time
        
        if elapsed >= self._wait:
            if self._leading:
                self._result = call()
                self._last_time = now
        else:
            if self._trailing and not self._timer:
                import threading
                self._timer = threading.Timer(self._wait - elapsed, lambda: (
                    setattr(self, '_last_time', time.time()),
                    self._result.__setitem__(0, call()) if isinstance(self._result, list) else None
                ))
                self._timer.start()
        
        return self._result[0] if isinstance(self._result, list) else self._result
    
    def cancel(self) -> None:
        """取消"""
        if self._timer:
            self._timer.cancel()
            self._timer = None


# 导出
__all__ = [
    "throttle",
    "Throttler",
]
