"""
Cleanup Registry - 清理注册表
基于 Claude Code cleanupRegistry.ts 设计

注册在优雅关闭时运行的清理函数。
"""
import atexit
import threading
from typing import Callable, Coroutine, Any

# 全局清理函数集合
_cleanup_functions: set[Callable[[], Any]] = set()
_cleanup_lock = threading.Lock()


def register_cleanup(cleanup_fn: Callable[[], Any]) -> Callable[[], None]:
    """
    注册清理函数
    
    Args:
        cleanup_fn: 清理函数（同步或异步）
        
    Returns:
        取消注册函数
    """
    with _cleanup_lock:
        _cleanup_functions.add(cleanup_fn)
    
    def unregister() -> None:
        with _cleanup_lock:
            _cleanup_functions.discard(cleanup_fn)
    
    return unregister


async def run_cleanup_functions() -> None:
    """
    运行所有注册的清理函数
    """
    with _cleanup_lock:
        functions = list(_cleanup_functions)
    
    # 并发执行所有清理函数
    import asyncio
    
    tasks = []
    for fn in functions:
        try:
            result = fn()
            if result is not None and hasattr(result, '__await__'):
                tasks.append(result)
            else:
                tasks.append(None)
        except Exception:
            pass
    
    # 等待所有异步清理完成
    async_tasks = [t for t in tasks if t is not None]
    if async_tasks:
        await asyncio.gather(*async_tasks, return_exceptions=True)


def run_cleanup_functions_sync() -> None:
    """
    同步运行所有清理函数
    """
    with _cleanup_lock:
        functions = list(_cleanup_functions)
    
    for fn in functions:
        try:
            fn()
        except Exception:
            pass


# 注册atexit清理
def _cleanup_atexit() -> None:
    """atexit回调"""
    run_cleanup_functions_sync()

try:
    atexit.register(_cleanup_atexit)
except Exception:
    pass


# 导出
__all__ = [
    "register_cleanup",
    "run_cleanup_functions",
    "run_cleanup_functions_sync",
]
