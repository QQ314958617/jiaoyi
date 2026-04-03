"""
OpenClaw Hooks System
======================
Inspired by Claude Code's hooks.ts (5022 lines) and registerSkillHooks.ts.

核心概念：
- HookEvent: 钩子可以触发的事件类型
- HookCallback: 钩子回调函数
- Hook: 已注册的钩子定义
- HookManager: 全局钩子管理器

支持的事件：
- on_trade: 交易执行前后
- on_market_data: 市场数据获取后
- on_review: 复盘写入前后
- on_startup: 系统启动时
- on_shutdown: 系统关闭时
- on_error: 错误发生时
- before_tool_call: 工具调用前
- after_tool_call: 工具调用后

注册方式：
1. 代码注册: hooks.register("on_trade", my_callback)
2. 配置文件: ~/.openclaw/hooks.json
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from pathlib import Path


# ============================================================================
# 事件类型
# ============================================================================

class HookEvent(str, Enum):
    """支持的钩子事件"""
    # 系统生命周期
    ON_STARTUP = "on_startup"          # 系统启动
    ON_SHUTDOWN = "on_shutdown"       # 系统关闭
    ON_ERROR = "on_error"            # 错误发生

    # 交易相关
    ON_TRADE = "on_trade"            # 交易执行（买卖）
    ON_TRADE_BEFORE = "on_trade_before"   # 交易执行前
    ON_TRADE_AFTER = "on_trade_after"     # 交易执行后

    # 市场数据
    ON_MARKET_DATA = "on_market_data"   # 市场数据获取后
    ON_MARKET_ALERT = "on_market_alert"  # 市场预警触发

    # 复盘相关
    ON_REVIEW = "on_review"          # 复盘写入
    ON_REVIEW_BEFORE = "on_review_before"
    ON_REVIEW_AFTER = "on_review_after"

    # 工具调用
    BEFORE_TOOL_CALL = "before_tool_call"   # 工具调用前
    AFTER_TOOL_CALL = "after_tool_call"     # 工具调用后

    # 心跳
    ON_HEARTBEAT = "on_heartbeat"     # 心跳触发


# ============================================================================
# 钩子回调
# ============================================================================

@dataclass
class Hook:
    """已注册的钩子"""
    id: str
    event: HookEvent
    callback: Callable
    description: str = ""
    enabled: bool = True
    async_mode: bool = False          # 是否异步执行
    timeout: float = 30.0            # 超时秒数
    tags: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    # 调用统计
    call_count: int = 0
    last_called: Optional[float] = None
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event": self.event.value if isinstance(self.event, Enum) else self.event,
            "description": self.description,
            "enabled": self.enabled,
            "async_mode": self.async_mode,
            "timeout": self.timeout,
            "tags": list(self.tags),
            "call_count": self.call_count,
            "last_called": self.last_called,
            "last_error": self.last_error,
        }


@dataclass
class HookContext:
    """
    传递给钩子回调的上下文。

    包含事件相关的全部信息。
    """
    event: HookEvent
    timestamp: float = field(default_factory=time.time)
    # 事件相关数据
    data: Dict[str, Any] = field(default_factory=dict)
    # 错误信息（ON_ERROR 事件）
    error: Optional[Exception] = None
    # 原始工具调用（before_tool_call / after_tool_call）
    tool_name: Optional[str] = None
    tool_input: Optional[Dict] = None
    tool_result: Any = None


# ============================================================================
# 钩子结果
# ============================================================================

@dataclass
class HookResult:
    """钩子执行结果"""
    hook_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    skipped: bool = False          # 条件未满足，跳过

    @classmethod
    def skipped(cls, hook_id: str) -> "HookResult":
        return cls(hook_id=hook_id, success=True, skipped=True)


# ============================================================================
# 钩子管理器
# ============================================================================

class HookManager:
    """
    全局钩子管理器。

    管理所有钩子的注册、发现、执行。

    用法:
        # 注册钩子
        def on_trade(ctx: HookContext):
            print(f"交易执行: {ctx.data}")

        hooks.register(on_trade, HookEvent.ON_TRADE)

        # 或者用装饰器
        @hooks.on(HookEvent.ON_TRADE)
        def my_trade_hook(ctx):
            ...

        # 触发钩子
        results = hooks.trigger(HookEvent.ON_TRADE, data={"action": "buy", "code": "600362"})
    """

    def __init__(self):
        self._hooks: Dict[HookEvent, List[Hook]] = {event: [] for event in HookEvent}
        self._lock = threading.RLock()
        self._hooks_dir = Path.home() / ".openclaw" / "hooks"
        self._config_file = self._hooks_dir / "hooks.json"
        self._seq = 0
        self._initialized = False

    # -------------------------------------------------------------------------
    # 注册
    # -------------------------------------------------------------------------

    def register(
        self,
        callback: Callable,
        event: HookEvent,
        description: str = "",
        enabled: bool = True,
        async_mode: bool = False,
        timeout: float = 30.0,
        tags: Optional[Set[str]] = None,
        hook_id: Optional[str] = None,
    ) -> Hook:
        """
        注册一个钩子。

        Returns:
            Hook 对象
        """
        with self._lock:
            self._seq += 1
            hook = Hook(
                id=hook_id or f"hook-{self._seq}",
                event=event,
                callback=callback,
                description=description,
                enabled=enabled,
                async_mode=async_mode,
                timeout=timeout,
                tags=tags or set(),
            )
            self._hooks[event].append(hook)
            return hook

    def on(self, event: HookEvent, **kwargs) -> Callable:
        """
        装饰器用法：

            @hooks.on(HookEvent.ON_TRADE)
            def my_trade_hook(ctx: HookContext):
                ...
        """
        def decorator(func: Callable) -> Callable:
            self.register(func, event, **kwargs)
            return func
        return decorator

    def unregister(self, hook_id: str) -> bool:
        """注销钩子"""
        with self._lock:
            for event_hooks in self._hooks.values():
                for i, h in enumerate(event_hooks):
                    if h.id == hook_id:
                        event_hooks.pop(i)
                        return True
            return False

    def enable(self, hook_id: str) -> bool:
        """启用钩子"""
        hook = self._find_hook(hook_id)
        if hook:
            hook.enabled = True
            return True
        return False

    def disable(self, hook_id: str) -> bool:
        """禁用钩子"""
        hook = self._find_hook(hook_id)
        if hook:
            hook.enabled = False
            return True
        return False

    def _find_hook(self, hook_id: str) -> Optional[Hook]:
        with self._lock:
            for hooks in self._hooks.values():
                for h in hooks:
                    if h.id == hook_id:
                        return h
        return None

    # -------------------------------------------------------------------------
    # 触发
    # -------------------------------------------------------------------------

    def trigger(
        self,
        event: HookEvent,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ) -> List[HookResult]:
        """
        触发指定事件的所有钩子。

        同步执行：所有钩子顺序执行，任一失败不影响其他。
        异步执行：使用线程池并发执行。

        Returns:
            List[HookResult]
        """
        ctx = HookContext(event=event, data=data or {}, error=error)
        results = []

        with self._lock:
            hooks = [h for h in self._hooks.get(event, []) if h.enabled]

        for hook in hooks:
            result = self._execute_hook(hook, ctx)
            results.append(result)

        return results

    def _execute_hook(self, hook: Hook, ctx: HookContext) -> HookResult:
        """执行单个钩子"""
        import time
        start = time.time()

        try:
            # 调用回调
            result = hook.callback(ctx)

            # 处理返回值的两种形式
            # 1. 直接返回数据
            # 2. 返回 HookResult

            if isinstance(result, HookResult):
                hook_result = result
            else:
                hook_result = HookResult(
                    hook_id=hook.id,
                    success=True,
                    data=result,
                    execution_time_ms=(time.time() - start) * 1000,
                )

            hook.call_count += 1
            hook.last_called = time.time()
            hook.last_error = None

            return hook_result

        except Exception as e:
            hook.call_count += 1
            hook.last_called = time.time()
            hook.last_error = str(e)

            return HookResult(
                hook_id=hook.id,
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000,
            )

    # -------------------------------------------------------------------------
    # 查询
    # -------------------------------------------------------------------------

    def list_hooks(self, event: Optional[HookEvent] = None) -> List[Hook]:
        """列出钩子"""
        with self._lock:
            if event:
                return list(self._hooks.get(event, []))
            all_hooks = []
            for hooks in self._hooks.values():
                all_hooks.extend(hooks)
            return all_hooks

    def list_by_tag(self, tag: str) -> List[Hook]:
        """按标签列出钩子"""
        with self._lock:
            result = []
            for hooks in self._hooks.values():
                result.extend(h for h in hooks if tag in h.tags)
            return result

    def stats(self) -> Dict[str, Any]:
        """钩子系统统计"""
        with self._lock:
            total = sum(len(h) for h in self._hooks.values())
            enabled = sum(1 for h in self._hooks.values() for h in h if h.enabled)
            return {
                "total_hooks": total,
                "enabled": enabled,
                "by_event": {
                    event.value: len(hooks)
                    for event, hooks in self._hooks.items()
                },
                "hooks_dir": str(self._hooks_dir),
                "config_file": str(self._config_file),
            }


# ============================================================================
# 预置钩子
# ============================================================================

# 全局钩子管理器单例
hooks = HookManager()


# ============================================================================
# 便捷装饰器
# ============================================================================

def on_startup(func: Callable) -> Callable:
    """@on_startup 装饰器"""
    return hooks.on(HookEvent.ON_STARTUP)(func)


def on_shutdown(func: Callable) -> Callable:
    """@on_shutdown 装饰器"""
    return hooks.on(HookEvent.ON_SHUTDOWN)(func)


def on_trade(func: Callable) -> Callable:
    """@on_trade 装饰器"""
    return hooks.on(HookEvent.ON_TRADE)(func)


def on_trade_before(func: Callable) -> Callable:
    """@on_trade_before 装饰器"""
    return hooks.on(HookEvent.ON_TRADE_BEFORE)(func)


def on_trade_after(func: Callable) -> Callable:
    """@on_trade_after 装饰器"""
    return hooks.on(HookEvent.ON_TRADE_AFTER)(func)


def on_review(func: Callable) -> Callable:
    """@on_review 装饰器"""
    return hooks.on(HookEvent.ON_REVIEW)(func)


def on_error(func: Callable) -> Callable:
    """@on_error 装饰器"""
    return hooks.on(HookEvent.ON_ERROR)(func)


def on_heartbeat(func: Callable) -> Callable:
    """@on_heartbeat 装饰器"""
    return hooks.on(HookEvent.ON_HEARTBEAT)(func)


# ============================================================================
# 集成点
# ============================================================================

def trigger_startup() -> List[HookResult]:
    """触发系统启动钩子"""
    return hooks.trigger(HookEvent.ON_STARTUP)


def trigger_shutdown() -> List[HookResult]:
    """触发系统关闭钩子"""
    return hooks.trigger(HookEvent.ON_SHUTDOWN)


def trigger_trade(action: str, stock_code: str, shares: int, result: Any) -> List[HookResult]:
    """触发交易钩子"""
    data = {"action": action, "stock_code": stock_code, "shares": shares, "result": result}
    before = hooks.trigger(HookEvent.ON_TRADE_BEFORE, data=data)
    after = hooks.trigger(HookEvent.ON_TRADE_AFTER, data=data)
    return before + after


def trigger_error(error: Exception, context: Optional[Dict] = None) -> List[HookResult]:
    """触发错误钩子"""
    return hooks.trigger(HookEvent.ON_ERROR, data=context or {}, error=error)


def trigger_market_data(data: Dict[str, Any]) -> List[HookResult]:
    """触发市场数据钩子"""
    return hooks.trigger(HookEvent.ON_MARKET_DATA, data=data)


def trigger_heartbeat() -> List[HookResult]:
    """触发心跳钩子"""
    return hooks.trigger(HookEvent.ON_HEARTBEAT)
