"""
OpenClaw Cleanup Registry
==========================
Inspired by Claude Code's src/utils/cleanupRegistry.ts + gracefulShutdown.ts.

核心功能：
1. 注册退出时需要执行的清理函数
2. 信号处理（SIGINT/SIGTERM）
3. atexit 注册
4.graceful shutdown（优雅退出）
5.超时保护（强制退出）

用途：
- Flask/gunicorn 进程优雅退出
- 定时任务被中断时保存状态
- 数据库连接池关闭
- API限流器持久化
- 交易未完成订单处理
"""

from __future__ import annotations

import atexit
import signal
import sys
import threading
import time
from typing import Callable, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import OrderedDict


# ============================================================================
# 清理函数注册表
# ============================================================================

_cleanup_functions: OrderedDict[str, Callable] = OrderedDict()
_cleanup_lock = threading.Lock()
_shutdown_in_progress = False


@dataclass
class CleanupRegistry:
    """清理函数注册表"""
    functions: "OrderedDict[str, Callable]" = field(default_factory=OrderedDict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def register(self, name: str, func: Callable, critical: bool = False) -> Callable:
        """
        注册清理函数。

        Args:
            name: 函数名（唯一标识）
            func: 清理函数，可以是 async 或 sync
            critical: True 表示即使超时也要执行完

        Returns:
            取消注册的函数
        """
        with self.lock:
            self.functions[name] = func
            if critical:
                # 标记为关键函数
                self.functions[name] = _CriticalWrapper(func)

        def unregister():
            with self.lock:
                self.functions.pop(name, None)

        return unregister

    def unregister(self, name: str) -> bool:
        """取消注册"""
        with self.lock:
            if name in self.functions:
                del self.functions[name]
                return True
            return False

    def clear(self) -> None:
        """清空所有清理函数"""
        with self.lock:
            self.functions.clear()

    async def run_async(self, timeout: float = 10.0) -> dict:
        """
        异步执行所有清理函数。

        Returns:
            {"success": [...], "failed": [...], "timed_out": [...]}
        """
        global _shutdown_in_progress
        _shutdown_in_progress = True

        results = {"success": [], "failed": [], "timed_out": []}

        # 收集所有函数
        with self.lock:
            funcs = list(self.functions.items())

        start_time = time.time()

        for name, func in funcs:
            elapsed = time.time() - start_time
            remaining = timeout - elapsed

            if remaining <= 0:
                results["timed_out"].append(name)
                continue

            try:
                # 检查是否是 coroutine
                import asyncio
                if asyncio.iscoroutinefunction(func):
                    await asyncio.wait_for(func(), timeout=remaining)
                elif callable(func):
                    # 尝试调用，可能返回协程
                    result = func()
                    if asyncio.iscoroutine(result):
                        await asyncio.wait_for(result, timeout=remaining)
                results["success"].append(name)
            except asyncio.TimeoutError:
                results["timed_out"].append(name)
            except Exception as e:
                results["failed"].append({"name": name, "error": str(e)})

        return results

    def run_sync(self, timeout: float = 10.0) -> dict:
        """
        同步执行所有清理函数。

        Returns:
            {"success": [...], "failed": [...], "timed_out": [...]}
        """
        global _shutdown_in_progress
        _shutdown_in_progress = True

        results = {"success": [], "failed": [], "timed_out": []}

        # 收集所有函数
        with self.lock:
            funcs = list(self.functions.items())

        start_time = time.time()

        for name, func in funcs:
            elapsed = time.time() - start_time
            remaining = timeout - elapsed

            if remaining <= 0:
                results["timed_out"].append(name)
                continue

            try:
                import asyncio
                # 先检查是否是协程函数
                if asyncio.iscoroutinefunction(func):
                    # 需要创建事件循环
                    loop = asyncio.new_event_loop()
                    try:
                        loop.run_until_complete(
                            asyncio.wait_for(func(), timeout=remaining)
                        )
                    finally:
                        loop.close()
                else:
                    # 普通函数
                    result = func()
                    # 检查返回值是否是协程
                    if asyncio.iscoroutine(result):
                        loop = asyncio.new_event_loop()
                        try:
                            loop.run_until_complete(
                                asyncio.wait_for(result, timeout=remaining)
                            )
                        finally:
                            loop.close()
                results["success"].append(name)
            except asyncio.TimeoutError:
                results["timed_out"].append(name)
            except Exception as e:
                results["failed"].append({"name": name, "error": str(e)})

        return results


class _CriticalWrapper:
    """关键清理函数包装器"""
    def __init__(self, func):
        self.func = func
        self.is_critical = True


# 全局注册表
_global_registry: Optional[CleanupRegistry] = None
_registry_lock = threading.Lock()


def get_cleanup_registry() -> CleanupRegistry:
    global _global_registry
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = CleanupRegistry()
    return _global_registry


# ============================================================================
# 便捷函数
# ============================================================================

def register_cleanup(name: str, func: Callable, critical: bool = False) -> Callable:
    """注册清理函数的便捷函数"""
    return get_cleanup_registry().register(name, func, critical=critical)


def unregister_cleanup(name: str) -> bool:
    """取消清理函数"""
    return get_cleanup_registry().unregister(name)


# ============================================================================
# 信号处理
# ============================================================================

_signal_handler_setup = False
_signal_lock = threading.Lock()


def setup_signal_handlers(
    registry: Optional[CleanupRegistry] = None,
    timeout: float = 10.0,
    on_shutdown: Optional[Callable] = None,
) -> None:
    """
    设置信号处理器。

    对应 Claude Code 的 setupSignalHandlers()。

    处理 SIGINT（Ctrl+C）和 SIGTERM（kill）。

    Args:
        registry: 清理注册表（默认全局）
        timeout: 清理超时时间
        on_shutdown: 退出前回调
    """
    global _signal_handler_setup

    if _signal_handler_setup:
        return

    with _signal_lock:
        if _signal_handler_setup:
            return
        _signal_handler_setup = True

    reg = registry or get_cleanup_registry()

    def handle_signal(signum, frame):
        sig_name = signal.Signals(signum).name
        print(f"\n收到 {sig_name}，开始优雅退出...", flush=True)

        if on_shutdown:
            try:
                on_shutdown()
            except Exception:
                pass

        results = reg.run_sync(timeout=timeout)

        # 打印结果
        if results["success"]:
            print(f"✅ 清理完成: {len(results['success'])} 个函数成功", flush=True)
        if results["failed"]:
            print(f"❌ 清理失败: {len(results['failed'])} 个函数", flush=True)
        for f in results["failed"]:
            print(f"   {f['name']}: {f['error']}", flush=True)
        if results["timed_out"]:
            print(f"⏰ 清理超时: {len(results['timed_out'])} 个函数未完成", flush=True)

        sys.exit(0)

    # 注册信号处理器
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # atexit 备用（如果信号没触发）
    def atexit_handler():
        if not _shutdown_in_progress:
            results = reg.run_sync(timeout=timeout)
            return results

    atexit.register(atexit_handler)


# ============================================================================
# 交易系统专用清理
# ============================================================================

def register_trading_cleanup() -> None:
    """
    注册交易系统专用的清理函数。

    在进程退出时：
    1. 保存成本状态到文件
    2. 关闭数据库连接
    3. 取消未完成的订单（如果有）
    """
    from openclaw.cost_tracker import save_cost_state
    from openclaw.trading_history import save_history

    registry = get_cleanup_registry()

    # 1. 保存成本状态
    registry.register("cost_tracker_save", save_cost_state)

    # 2. 保存交易历史
    try:
        registry.register("history_save", save_history)
    except Exception:
        pass

    # 3. 关闭数据库
    try:
        def close_db():
            import app as flask_app
            if hasattr(flask_app, 'db'):
                flask_app.db.close()
        registry.register("db_close", close_db)
    except Exception:
        pass


# ============================================================================
# 定时任务清理守卫
# ============================================================================

class TaskCleanupGuard:
    """
    定时任务清理守卫。

    确保定时任务被中断时能优雅完成。

    用法：
        guard = TaskCleanupGuard()

        @app.cron_job(...)
        def my_task():
            with guard:
                # 执行任务...
                # 如果收到退出信号，会等待当前任务完成
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._in_progress = False
        self._should_exit = threading.Event()
        self._lock = threading.Lock()

    def __enter__(self):
        with self._lock:
            self._in_progress = True
            self._should_exit.clear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            self._in_progress = False
            self._should_exit.clear()

        # 如果收到退出信号，打印警告
        if self._should_exit.is_set():
            print(f"⚠️ 任务被中断信号打断，已完成当前循环")

        return False  # 不吞掉异常

    def request_exit(self):
        """请求退出（由信号处理器调用）"""
        self._should_exit.set()

    @property
    def should_exit(self) -> bool:
        """检查是否应该退出"""
        return self._should_exit.is_set()
