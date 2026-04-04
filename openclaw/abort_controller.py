"""
Abort Controller - 中断控制器
基于 Claude Code abortController.ts 设计

提供AbortController的封装和子控制器创建。
"""
import threading
import weakref
from typing import Optional


class AbortController:
    """
    中断控制器
    
    用于取消异步操作。
    """
    
    def __init__(self):
        self._signal = AbortSignal()
        self._aborted = False
        self._reason: Optional[Exception] = None
    
    @property
    def signal(self) -> 'AbortSignal':
        """获取中断信号"""
        return self._signal
    
    def abort(self, reason: Optional[Exception] = None) -> None:
        """
        中断操作
        
        Args:
            reason: 中断原因
        """
        if self._aborted:
            return
        
        self._aborted = True
        self._reason = reason
        self._signal._notify_abort(reason)
    
    @property
    def aborted(self) -> bool:
        """是否已中断"""
        return self._aborted
    
    @property
    def reason(self) -> Optional[Exception]:
        """获取中断原因"""
        return self._reason


class AbortSignal:
    """
    中断信号
    
    包含中断状态和回调函数。
    """
    
    def __init__(self):
        self._aborted = False
        self._reason: Optional[Exception] = None
        self._abort_handlers: list[callable] = []
        self._lock = threading.Lock()
    
    @property
    def aborted(self) -> bool:
        """是否已中断"""
        return self._aborted
    
    @property
    def reason(self) -> Optional[Exception]:
        """获取中断原因"""
        return self._reason
    
    def _notify_abort(self, reason: Optional[Exception]) -> None:
        """通知所有中断处理器"""
        with self._lock:
            self._aborted = True
            self._reason = reason
            handlers = list(self._abort_handlers)
        
        for handler in handlers:
            try:
                handler(reason)
            except Exception:
                pass  # 忽略处理器中的错误
    
    def add_event_listener(
        self,
        event: str,
        handler: callable,
        once: bool = False,
    ) -> None:
        """
        添加事件监听器
        
        Args:
            event: 事件名（只支持'abort'）
            handler: 处理函数
            once: 是否只执行一次
        """
        if event != 'abort':
            return
        
        with self._lock:
            if once:
                # 包装为一次性处理器
                def once_handler(reason):
                    self.remove_event_listener(event, once_handler)
                    handler(reason)
                self._abort_handlers.append(once_handler)
            else:
                self._abort_handlers.append(handler)
    
    def remove_event_listener(self, event: str, handler: callable) -> None:
        """
        移除事件监听器
        
        Args:
            event: 事件名
            handler: 处理函数
        """
        if event != 'abort':
            return
        
        with self._lock:
            if handler in self._abort_handlers:
                self._abort_handlers.remove(handler)
    
    def throw_if_aborted(self) -> None:
        """如果已中断则抛出异常"""
        if self._aborted and self._reason:
            raise self._reason


def create_abort_controller() -> AbortController:
    """
    创建AbortController
    
    Returns:
        新的中断控制器
    """
    return AbortController()


def create_child_abort_controller(parent: AbortController) -> AbortController:
    """
    创建子中断控制器
    
    当父控制器中断时，子控制器也会中断。
    中断子控制器不影响父控制器。
    
    Args:
        parent: 父中断控制器
        
    Returns:
        子中断控制器
    """
    child = AbortController()
    
    # 快速路径：父已中断
    if parent.aborted:
        child.abort(parent.reason)
        return child
    
    # 使用弱引用避免内存泄漏
    parent_ref = weakref.ref(parent)
    child_ref = weakref.ref(child)
    
    def propagate_abort(reason):
        parent = parent_ref()
        child = child_ref()
        if child and not child.aborted:
            child.abort(reason)
    
    # 添加一次性监听
    parent.signal.add_event_listener('abort', propagate_abort, once=True)
    
    # 当子中断时，移除父监听器
    def cleanup(reason):
        parent = parent_ref()
        if parent:
            try:
                parent.signal.remove_event_listener('abort', propagate_abort)
            except ValueError:
                pass  # 已移除
    
    child.signal.add_event_listener('abort', cleanup, once=True)
    
    return child


# 导出
__all__ = [
    "AbortController",
    "AbortSignal",
    "create_abort_controller",
    "create_child_abort_controller",
]
