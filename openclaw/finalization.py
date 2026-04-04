"""
Finalization - 最终化
基于 Claude Code finalization.ts 设计

资源清理工具。
"""
import atexit
from typing import Callable, Optional


class FinalizationRegistry:
    """
    最终化注册表
    
    注册在对象被垃圾回收时调用的回调。
    """
    
    def __init__(self):
        self._callbacks = {}
    
    def register(self, target: object, callback: Callable, *args) -> None:
        """
        注册最终化回调
        
        Args:
            target: 目标对象
            callback: 回调函数
            *args: 回调参数
        """
        import gc
        import id
        
        obj_id = id(target)
        self._callbacks[obj_id] = (callback, args)
        
        # 注意：Python的gc没有直接finalization机制
        # 这里用__del__模拟
        target.__finalization_callback__ = lambda: callback(*args)
    
    def unregister(self, target: object) -> None:
        """取消注册"""
        import id
        obj_id = id(target)
        self._callbacks.pop(obj_id, None)


class Cleanup:
    """
    清理工具
    
    使用上下文管理器确保清理。
    """
    
    def __init__(self):
        self._cleanup_funcs = []
    
    def register(self, func: Callable, *args, **kwargs) -> None:
        """注册清理函数"""
        self._cleanup_funcs.append((func, args, kwargs))
    
    def cleanup(self) -> None:
        """执行所有清理"""
        for func, args, kwargs in reversed(self._cleanup_funcs):
            try:
                func(*args, **kwargs)
            except Exception:
                pass
        
        self._cleanup_funcs.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.cleanup()


def cleanup_on_exit(func: Callable) -> Callable:
    """
    退出时清理装饰器
    
    Args:
        func: 清理函数
        
    Returns:
        装饰器
    """
    atexit.register(func)
    return func


class Resource:
    """
    资源封装
    
    自动管理资源的获取和释放。
    """
    
    def __init__(
        self,
        acquire: Callable,
        release: Callable,
    ):
        """
        Args:
            acquire: 获取资源的函数
            release: 释放资源的函数
        """
        self._acquire = acquire
        self._release = release
        self._resource = None
    
    def __enter__(self):
        self._resource = self._acquire()
        return self._resource
    
    def __exit__(self, *args):
        if self._resource:
            self._release(self._resource)


# 导出
__all__ = [
    "FinalizationRegistry",
    "Cleanup",
    "cleanup_on_exit",
    "Resource",
]
