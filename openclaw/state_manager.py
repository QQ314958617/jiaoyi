"""
OpenClaw State Manager
=======================
Inspired by Claude Code's AppState.tsx + AppStateStore.ts + store.ts.

核心设计：
1. AppState - 全局应用状态（不可变）
2. Store - 状态存储（getState/setState/subscribe）
3. StateSlice - 按需订阅状态切片
4. Settings 管理 - 设置变更处理
5. 发布订阅模式 - 状态变化自动通知

Claude Code 的状态管理：
- AppState = 大型不可变状态对象
- AppStateStore = Zustand 风格 store
- useAppState = React hook，按需订阅
- applySettingsChange = 设置变更处理器
"""

from __future__ import annotations

import threading
import time
import copy
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from collections import defaultdict


# ============================================================================
# 状态变更事件
# ============================================================================

@dataclass
class StateChangeEvent:
    """状态变更事件"""
    key: str
    old_value: Any
    new_value: Any
    timestamp: float = field(default_factory=time.time)


# ============================================================================
# AppState - 应用状态
# ============================================================================

@dataclass
class AppState:
    """
    全局应用状态。

    对应 Claude Code 的 AppState 类型。
    包含所有全局可访问的状态字段。
    """

    # 状态字段
    verbose: bool = False
    model: str = "default"
    status_text: str = ""
    expanded_view: str = "none"  # none / tasks / teammates

    # 设置相关
    settings: Dict[str, Any] = field(default_factory=dict)

    # 任务相关
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    active_task_id: Optional[str] = None

    # 工具相关
    tool_permission_mode: str = "accepted_edits"
    allowed_paths: List[str] = field(default_factory=list)

    # MCP 相关
    mcp_servers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    mcp_tools: List[Dict[str, Any]] = field(default_factory=list)

    # Agent 相关
    agent_definitions: List[Dict[str, Any]] = field(default_factory=list)
    active_agents: Dict[str, str] = field(default_factory=dict)  # name -> agent_id

    # 时间戳
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "verbose": self.verbose,
            "model": self.model,
            "status_text": self.status_text,
            "expanded_view": self.expanded_view,
            "settings": copy.deepcopy(self.settings),
            "tasks": copy.deepcopy(self.tasks),
            "active_task_id": self.active_task_id,
            "tool_permission_mode": self.tool_permission_mode,
            "allowed_paths": list(self.allowed_paths),
            "mcp_servers": copy.deepcopy(self.mcp_servers),
            "mcp_tools": copy.deepcopy(self.mcp_tools),
            "agent_definitions": copy.deepcopy(self.agent_definitions),
            "active_agents": dict(self.active_agents),
            "last_updated": self.last_updated,
        }


# ============================================================================
# Store - 状态存储
# ============================================================================

class Store:
    """
    状态存储。

    对应 Claude Code 的 AppStateStore (Zustand风格)。
    支持 getState/setState/subscribe。
    """

    def __init__(self, initial_state: Optional[AppState] = None):
        self._state = initial_state or AppState()
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)
        self._all_listeners: List[Callable] = []
        self._lock = threading.RLock()
        self._version = 0  # 乐观并发控制

    def get_state(self) -> AppState:
        """获取当前状态"""
        with self._lock:
            return copy.deepcopy(self._state)

    def get_state_field(self, key: str) -> Any:
        """获取单个字段"""
        with self._lock:
            return getattr(self._state, key, None)

    def set_state(self, update: Dict[str, Any]) -> None:
        """
        设置状态。

        对应 Claude Code 的 store.setState()。
        支持部分更新（只更新指定的字段）。
        """
        with self._lock:
            old_state = copy.deepcopy(self._state)

            # 更新字段
            for key, value in update.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)

            self._state.last_updated = time.time()
            self._version += 1

            # 触发监听器
            self._notify_listeners(old_state, update)

    def set_state_with_action(
        self,
        action: Callable[[AppState], Dict[str, Any]]
    ) -> None:
        """
        通过 action 函数更新状态。

        action 接收当前状态，返回要更新的字段。
        """
        with self._lock:
            old_state = copy.deepcopy(self._state)
            update = action(self._state)
            for key, value in update.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)
            self._state.last_updated = time.time()
            self._version += 1
            self._notify_listeners(old_state, update)

    def _notify_listeners(self, old_state: AppState, update: Dict[str, Any]) -> None:
        """通知监听器"""
        # 按 key 的监听器
        for key in update:
            for listener in self._listeners.get(key, []):
                try:
                    listener(update[key], old_state)
                except Exception:
                    pass

        # 全量监听器
        event = StateChangeEvent(
            key="*",
            old_value=old_state,
            new_value=self._state
        )
        for listener in self._all_listeners:
            try:
                listener(event)
            except Exception:
                pass

    # ---------------------
    # 订阅
    # ---------------------

    def subscribe(
        self,
        key: str,
        listener: Callable[[Any, Any], None]
    ) -> Callable:
        """
        订阅状态变化。

        Returns:
            取消订阅的函数
        """
        self._listeners[key].append(listener)

        def unsubscribe():
            if listener in self._listeners[key]:
                self._listeners[key].remove(listener)

        return unsubscribe

    def subscribe_all(
        self,
        listener: Callable[[StateChangeEvent], None]
    ) -> Callable:
        """
        订阅所有状态变化。

        Returns:
            取消订阅的函数
        """
        self._all_listeners.append(listener)

        def unsubscribe():
            if listener in self._all_listeners:
                self._all_listeners.remove(listener)

        return unsubscribe

    def subscribe_many(
        self,
        keys: List[str],
        listener: Callable[[Dict[str, Any]], None]
    ) -> Callable:
        """
        订阅多个状态字段。

        当任何一个字段变化时触发。
        Returns:
            取消订阅的函数
        """
        per_key_listeners = {key: [] for key in keys}

        def combined_listener(event: StateChangeEvent):
            try:
                listener({event.key: event.new_value})
            except Exception:
                pass

        for key in keys:
            self._listeners[key].append(combined_listener)
            per_key_listeners[key].append(combined_listener)

        def unsubscribe():
            for key in keys:
                for l in per_key_listeners[key]:
                    if l in self._listeners[key]:
                        self._listeners[key].remove(l)

        return unsubscribe

    @property
    def version(self) -> int:
        """当前版本号（乐观并发控制）"""
        return self._version


# ============================================================================
# 全局 Store
# ============================================================================

# 全局状态存储
_global_store: Optional[Store] = None
_store_lock = threading.Lock()


def get_global_store() -> Store:
    """获取全局 Store 单例"""
    global _global_store
    if _global_store is None:
        with _store_lock:
            if _global_store is None:
                _global_store = Store()
    return _global_store


def get_state() -> AppState:
    """获取当前状态"""
    return get_global_store().get_state()


def set_state(update: Dict[str, Any]) -> None:
    """设置状态"""
    get_global_store().set_state(update)


# ============================================================================
# 状态切片（类似 React 的 useAppState）
# ============================================================================

class StateSlice:
    """
    状态切片订阅器。

    类似 React 的 useAppState hook。
    当选中的值变化时，自动通知订阅者。
    """

    def __init__(
        self,
        store: Optional[Store] = None,
    ):
        self._store = store or get_global_store()
        self._callbacks: Dict[str, Callable] = {}
        self._last_values: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def select(self, key: str, callback: Callable[[Any], None]) -> Callable:
        """
        选择一个状态字段进行订阅。

        当该字段变化时，callback 会被调用。
        Returns:
            取消订阅的函数
        """
        with self._lock:
            # 获取初始值
            current = self._store.get_state_field(key)
            self._last_values[key] = current

            def wrapped_callback(new_value, old_value):
                # 比较是否真的变化了
                if new_value != old_value:
                    self._last_values[key] = new_value
                    try:
                        callback(new_value)
                    except Exception:
                        pass

            self._callbacks[key] = wrapped_callback
            unsubscribe = self._store.subscribe(key, wrapped_callback)

            return unsubscribe

    def select_many(
        self,
        keys: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ) -> Callable:
        """
        选择多个状态字段进行订阅。

        当任何一个字段变化时，callback 都会被调用。
        Returns:
            取消订阅的函数
        """
        return self._store.subscribe_many(keys, callback)


# ============================================================================
# 设置变更处理
# ============================================================================

def apply_settings_change(
    store: Store,
    changes: Dict[str, Any]
) -> None:
    """
    应用设置变更。

    对应 Claude Code 的 applySettingsChange()。
    处理设置的验证和生效。
    """
    current_state = store.get_state()

    # 合并设置变更
    new_settings = {**current_state.settings, **changes}

    # 验证设置值
    validated_changes = _validate_settings(changes)

    store.set_state({
        "settings": new_settings,
        **validated_changes,
    })


def _validate_settings(changes: Dict[str, Any]) -> Dict[str, Any]:
    """验证设置值"""
    validated = {}

    # 验证 verbose
    if "verbose" in changes:
        validated["verbose"] = bool(changes["verbose"])

    # 验证 model
    if "model" in changes:
        validated["model"] = str(changes["model"])

    # 验证 tool_permission_mode
    if "tool_permission_mode" in changes:
        mode = changes["tool_permission_mode"]
        if mode in {"accepted_edits", "bypass_permissions", "review_all", "review_some"}:
            validated["tool_permission_mode"] = mode

    # 验证 allowed_paths
    if "allowed_paths" in changes:
        paths = changes["allowed_paths"]
        if isinstance(paths, list):
            validated["allowed_paths"] = [str(p) for p in paths]

    return validated


# ============================================================================
# 状态管理工具
# ============================================================================

class StateManager:
    """
    高级状态管理器。

    提供更高级的状态管理功能：
    - 中间件支持
    - 状态历史
    - 快照
    """

    def __init__(self, store: Optional[Store] = None):
        self._store = store or get_global_store()
        self._history: List[Dict[str, Any]] = []
        self._max_history = 100
        self._middleware: List[Callable] = []
        self._lock = threading.Lock()

        # 订阅所有变更以记录历史
        self._store.subscribe_all(self._record_history)

    def add_middleware(self, middleware: Callable) -> None:
        """添加中间件"""
        self._middleware.append(middleware)

    def _record_history(self, event: StateChangeEvent) -> None:
        """记录状态变更历史"""
        with self._lock:
            self._history.append({
                "key": event.key,
                "timestamp": event.timestamp,
                "old_value": copy.deepcopy(event.old_value),
                "new_value": copy.deepcopy(event.new_value),
            })
            if len(self._history) > self._max_history:
                self._history.pop(0)

    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取状态变更历史"""
        with self._lock:
            return list(self._history[-limit:])

    def snapshot(self, name: str) -> Callable:
        """
        保存状态快照。

        返回一个恢复函数，可以将状态恢复到快照点。
        """
        snapshot_state = copy.deepcopy(self._store.get_state())

        def restore():
            self._store.set_state(snapshot_state.to_dict())

        return restore

    def can_undo(self) -> bool:
        """是否可以撤销"""
        with self._lock:
            return len(self._history) > 0

    def undo(self) -> bool:
        """
        撤销上一次状态变更。

        Returns:
            是否成功撤销
        """
        with self._lock:
            if not self._history:
                return False

            # 获取上一次变更前的状态
            last_change = self._history.pop()
            old_state = last_change["old_value"]

            if isinstance(old_state, AppState):
                self._store.set_state(old_state.to_dict())
            else:
                # old_value 是整个 state
                self._store.set_state(old_state.to_dict() if hasattr(old_state, 'to_dict') else old_state)

            return True


# ============================================================================
# 便捷函数
# ============================================================================

def update_state(**kwargs) -> None:
    """快捷更新状态"""
    get_global_store().set_state(kwargs)


def get_verbose() -> bool:
    """获取 verbose 模式"""
    return get_global_store().get_state_field("verbose")


def set_verbose(verbose: bool) -> None:
    """设置 verbose 模式"""
    get_global_store().set_state({"verbose": verbose})


def get_model() -> str:
    """获取当前模型"""
    return get_global_store().get_state_field("model")


def set_model(model: str) -> None:
    """设置当前模型"""
    get_global_store().set_state({"model": model})


def get_status_text() -> str:
    """获取状态文本"""
    return get_global_store().get_state_field("status_text")


def set_status_text(text: str) -> None:
    """设置状态文本"""
    get_global_store().set_state({"status_text": text})
