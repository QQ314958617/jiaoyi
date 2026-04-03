"""
OpenClaw Abort Controller
======================
Inspired by Claude Code's src/utils/abortController.ts.

AbortController 实现，支持：
1. 标准 AbortController
2. 父子级联取消
3. WeakRef 防止内存泄漏
"""

from __future__ import annotations

import asyncio, threading, weakref
from typing import Callable, Optional

# ============================================================================
# AbortController
# ============================================================================

class AbortError(Exception):
    """取消异常"""
    pass

class AbortController:
    """
    AbortController 实现
    
    用于取消异步操作。
    
    用法：
    ```python
    controller = AbortController()
    
    async def do_work(signal):
        try:
            async for item in stream(signal):
                if signal.aborted:
                    break
                process(item)
        except AbortError:
            pass
    
    # 取消
    controller.abort()
    
    # 或者作为上下文管理器
    async with controller:
        await do_work(controller.signal)
    ```
    """
    
    def __init__(self):
        self._aborted = False
        self._reason: Optional[Exception] = None
        self._callbacks: list[Callable] = []
        self._lock = threading.Lock()
    
    @property
    def aborted(self) -> bool:
        return self._aborted
    
    @property
    def reason(self) -> Optional[Exception]:
        return self._reason
    
    def abort(self, reason: Optional[Exception] = None) -> None:
        """取消操作"""
        with self._lock:
            if self._aborted:
                return
            
            self._aborted = True
            self._reason = reason or AbortError("Aborted")
            
            # 通知所有回调
            for callback in self._callbacks:
                try:
                    callback(self._reason)
                except Exception:
                    pass
            
            self._callbacks.clear()
    
    def add_callback(self, callback: Callable) -> None:
        """添加取消回调"""
        with self._lock:
            if self._aborted:
                callback(self._reason)
            else:
                self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable) -> None:
        """移除回调"""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def __enter__(self) -> 'AbortController':
        return self
    
    def __exit__(self, *args) -> None:
        self.abort()
    
    def __await__(self):
        """支持 await controller"""
        return self._aborted.__await__()


class Signal:
    """
    AbortSignal - 类似于 Web API 的 AbortSignal
    
    用于检查操作是否被取消。
    """
    
    def __init__(self, controller: AbortController):
        self._controller = controller
    
    @property
    def aborted(self) -> bool:
        return self._controller.aborted
    
    @property
    def reason(self) -> Optional[Exception]:
        return self._controller.reason
    
    def throw_if_aborted(self) -> None:
        """如果已取消则抛出异常"""
        if self._controller.aborted:
            raise self._controller.reason or AbortError("Aborted")


def create_abort_controller() -> AbortController:
    """创建 AbortController"""
    return AbortController()


# ============================================================================
# 父子级联取消
# ============================================================================

class ChildAbortController(AbortController):
    """
    子级 AbortController
    
    当父级取消时，子级自动取消。
    子级取消不影响父级。
    
    使用 WeakRef 防止内存泄漏。
    """
    
    def __init__(self, parent: AbortController):
        super().__init__()
        self._parent_ref = weakref.ref(parent)
        
        # 检查父级是否已取消
        if parent.aborted:
            self.abort(parent.reason)
            return
        
        # 绑定父级取消事件
        def on_parent_abort(reason):
            # 使用弱引用检查父级是否还存在
            if self._parent_ref() is not None:
                self.abort(reason)
        
        parent.add_callback(on_parent_abort)
        self._parent_callback = on_parent_abort
    
    def detach_from_parent(self) -> None:
        """从父级分离"""
        parent = self._parent_ref()
        if parent and hasattr(parent, 'remove_callback'):
            parent.remove_callback(self._parent_callback)


class AbortRegistry:
    """
    AbortController 注册表
    
    管理多个 AbortController，支持批量取消。
    """
    
    def __init__(self):
        self._controllers: dict[str, AbortController] = {}
        self._lock = threading.Lock()
    
    def create(self, name: str) -> AbortController:
        """创建并注册一个 AbortController"""
        with self._lock:
            if name in self._controllers:
                self._controllers[name].abort()
            
            controller = AbortController()
            self._controllers[name] = controller
            return controller
    
    def get(self, name: str) -> Optional[AbortController]:
        """获取已注册的 AbortController"""
        with self._lock:
            return self._controllers.get(name)
    
    def abort(self, name: str) -> bool:
        """取消指定的控制器"""
        with self._lock:
            if name in self._controllers:
                self._controllers[name].abort()
                return True
            return False
    
    def abort_all(self) -> None:
        """取消所有控制器"""
        with self._lock:
            for controller in self._controllers.values():
                controller.abort()
            self._controllers.clear()
    
    def remove(self, name: str) -> bool:
        """移除控制器"""
        with self._lock:
            if name in self._controllers:
                del self._controllers[name]
                return True
            return False


# ============================================================================
# 异步支持
# ============================================================================

async def wait_abort(controller: AbortController, timeout: Optional[float] = None) -> None:
    """
    等待 AbortController 被取消
    
    用法：
    ```python
    controller = AbortController()
    
    async with asyncio.timeout(5) if timeout else None:
        await wait_abort(controller)
    ```
    """
    loop = asyncio.get_event_loop()
    
    if controller.aborted:
        raise controller.reason or AbortError("Already aborted")
    
    future = loop.create_future()
    
    def on_abort(reason):
        if not future.done():
            future.set_exception(reason or AbortError("Aborted"))
    
    controller.add_callback(on_abort)
    
    try:
        await future
    finally:
        controller.remove_callback(on_abort)


class AbortScope:
    """
    Abort 作用域
    
    在作用域内的所有操作都可以被取消。
    
    用法：
    ```python
    scope = AbortScope()
    
    async with scope:
        await task1(scope.signal)
        await task2(scope.signal)
    
    # 取消所有
    scope.abort()
    ```
    """
    
    def __init__(self):
        self._controller = AbortController()
    
    @property
    def signal(self) -> Signal:
        return Signal(self._controller)
    
    @property
    def aborted(self) -> bool:
        return self._controller.aborted
    
    def abort(self, reason: Optional[Exception] = None) -> None:
        self._controller.abort(reason)
    
    async def __aenter__(self) -> 'AbortScope':
        return self
    
    async def __aexit__(self, *args) -> None:
        self.abort()
