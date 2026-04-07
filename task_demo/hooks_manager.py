"""
Hooks Manager - 钩子管理器
从 Claude Code src/utils/hooks/sessionHooks.ts 移植

功能：
1. 管理所有已注册的钩子
2. 按事件类型分组
3. 匹配并执行钩子
4. 支持会话级临时钩子
"""
import threading
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field

from hooks_base import (
    HookEvent,
    HookConfig,
    HookType,
    HookInput,
    HookOutput,
    HookExecutor,
    HookType,
)


@dataclass
class HookMatcher:
    """钩子匹配器"""
    matcher: str  # 匹配模式（工具名等）
    skill_root: Optional[str] = None  # 技能根目录
    hooks: List[HookConfig] = field(default_factory=list)


@dataclass
class SessionHookStore:
    """会话钩子存储"""
    hooks: Dict[HookEvent, List[HookMatcher]] = field(default_factory=dict)


class FunctionHook:
    """
    函数类型钩子（内联回调）
    Session-scoped only，不能持久化到配置文件
    """
    def __init__(
        self,
        callback: Callable[[HookInput], Any],
        error_message: str,
        timeout_ms: int = 5000,
        hook_id: Optional[str] = None,
    ):
        self.type = HookType.FUNCTION
        self.id = hook_id or f"fn-hook-{id(self)}"
        self.callback = callback
        self.error_message = error_message
        self.timeout_ms = timeout_ms


# 全局钩子管理器
class HooksManager:
    """
    钩子管理器 - 核心组件
    - 全局钩子注册表
    - 会话级临时钩子
    - 钩子匹配与执行
    """
    _instance: Optional["HooksManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._global_hooks: Dict[HookEvent, List[HookMatcher]] = {}
        self._session_hooks: Dict[str, SessionHookStore] = {}
        self._executor = HookExecutor()
        self._rwlock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "HooksManager":
        return cls()

    # ==================== 钩子注册 ====================

    def register_hook(
        self,
        config: HookConfig,
        session_id: Optional[str] = None,
    ) -> None:
        """
        注册钩子
        - session_id=None 表示全局钩子
        - session_id!=None 表示会话级临时钩子
        """
        event = config.event
        store = self._session_hooks.get(session_id) if session_id else None
        target = store.hooks if store else self._global_hooks

        with self._rwlock:
            if event not in target:
                target[event] = []

            # 查找或创建匹配器
            matcher = next(
                (m for m in target[event] if m.matcher == config.matcher),
                None
            )
            if matcher:
                matcher.hooks.append(config)
            else:
                target[event].append(HookMatcher(
                    matcher=config.matcher,
                    hooks=[config],
                ))

    def add_function_hook(
        self,
        event: HookEvent,
        matcher: str,
        callback: Callable[[HookInput], Any],
        error_message: str,
        session_id: Optional[str] = None,
        timeout_ms: int = 5000,
    ) -> str:
        """
        添加函数类型钩子
        返回 hook_id（用于后续删除）
        """
        hook = FunctionHook(
            callback=callback,
            error_message=error_message,
            timeout_ms=timeout_ms,
        )
        config = HookConfig(
            id=hook.id,
            name=hook.id,
            hook_type=HookType.FUNCTION,
            event=event,
            matcher=matcher,
            callback=callback,
            timeout_ms=timeout_ms,
        )
        self.register_hook(config, session_id)
        return hook.id

    def remove_function_hook(
        self,
        hook_id: str,
        event: HookEvent,
        session_id: Optional[str] = None,
    ) -> bool:
        """删除函数类型钩子"""
        store = self._session_hooks.get(session_id) if session_id else None
        target = store.hooks if store else self._global_hooks

        with self._rwlock:
            matchers = target.get(event, [])
            for matcher in matchers:
                matcher.hooks = [
                    h for h in matcher.hooks if h.id != hook_id
                ]
            return True

    # ==================== 钩子执行 ====================

    def fire(
        self,
        event: HookEvent,
        hook_input: HookInput,
        session_id: Optional[str] = None,
    ) -> List[HookOutput]:
        """
        触发钩子
        返回所有钩子的执行结果列表
        """
        results = []

        with self._rwlock:
            # 收集所有匹配的钩子
            configs = self._collect_matching_hooks(event, hook_input, session_id)

        # 执行每个钩子
        for config in configs:
            if config.hook_type == HookType.COMMAND:
                output = self._executor.execute_command(config, hook_input)
            elif config.hook_type == HookType.FUNCTION:
                output = self._executor.execute_function(config, hook_input)
            elif config.hook_type == HookType.HTTP:
                output = self.execute_http_hook(config, hook_input)
            else:
                continue

            results.append(output)

            # 如果是阻塞型结果，停止执行后续钩子
            if output.outcome == "blocking" or not output.continue_:
                break

        return results

    def _collect_matching_hooks(
        self,
        event: HookEvent,
        hook_input: HookInput,
        session_id: Optional[str],
    ) -> List[HookConfig]:
        """收集所有匹配的钩子"""
        configs = []

        # 全局钩子
        global_matchers = self._global_hooks.get(event, [])
        for matcher in global_matchers:
            if matcher.matcher == "*" or (
                hook_input.tool_name and
                self._match_pattern(matcher.matcher, hook_input.tool_name)
            ):
                configs.extend(matcher.hooks)

        # 会话级钩子
        if session_id:
            session_store = self._session_hooks.get(session_id)
            if session_store:
                session_matchers = session_store.hooks.get(event, [])
                for matcher in session_matchers:
                    if matcher.matcher == "*" or (
                        hook_input.tool_name and
                        self._match_pattern(matcher.matcher, hook_input.tool_name)
                    ):
                        configs.extend(matcher.hooks)

        return configs

    def _match_pattern(self, pattern: str, value: str) -> bool:
        """模式匹配"""
        if pattern == "*":
            return True
        import re
        regex = "^" + pattern.replace("*", ".*") + "$"
        return bool(re.match(regex, value))

    # ==================== 会话管理 ====================

    def create_session(self, session_id: str) -> None:
        """创建会话钩子存储"""
        with self._rwlock:
            self._session_hooks[session_id] = SessionHookStore()

    def destroy_session(self, session_id: str) -> None:
        """销毁会话钩子存储"""
        with self._rwlock:
            self._session_hooks.pop(session_id, None)

    # ==================== 快捷方法 ====================

    def on_session_start(
        self,
        callback: Callable[[HookInput], Any],
        session_id: Optional[str] = None,
    ) -> str:
        """快捷方法：注册会话开始钩子"""
        return self.add_function_hook(
            HookEvent.SESSION_START,
            "*",
            callback,
            "Session start hook failed",
            session_id,
        )

    def on_session_end(
        self,
        callback: Callable[[HookInput], Any],
        session_id: Optional[str] = None,
    ) -> str:
        """快捷方法：注册会话结束钩子"""
        return self.add_function_hook(
            HookEvent.SESSION_END,
            "*",
            callback,
            "Session end hook failed",
            session_id,
        )

    def on_pre_tool(
        self,
        tool_name: str,
        callback: Callable[[HookInput], Any],
        session_id: Optional[str] = None,
    ) -> str:
        """快捷方法：注册工具执行前钩子"""
        return self.add_function_hook(
            HookEvent.PRE_TOOL_USE,
            tool_name,
            callback,
            f"Pre-tool hook for {tool_name} failed",
            session_id,
        )

    def on_post_tool(
        self,
        tool_name: str,
        callback: Callable[[HookInput], Any],
        session_id: Optional[str] = None,
    ) -> str:
        """快捷方法：注册工具执行后钩子"""
        return self.add_function_hook(
            HookEvent.POST_TOOL_USE,
            tool_name,
            callback,
            f"Post-tool hook for {tool_name} failed",
            session_id,
        )

    # ==================== HTTP钩子 ====================

    def execute_http_hook(
        self,
        config: HookConfig,
        hook_input: HookInput,
    ) -> HookOutput:
        """执行HTTP钩子（需要外部HTTP库）"""
        try:
            import urllib.request
            import urllib.error

            if not config.url:
                return HookOutput(
                    outcome="non_blocking_error",
                    continue_=True,
                    reason="No URL configured for HTTP hook",
                )

            data = json.dumps(hook_input.to_dict()).encode("utf-8")
            req = urllib.request.Request(
                config.url,
                data=data,
                headers={"Content-Type": "application/json"},
                method=config.method,
            )

            with urllib.request.urlopen(req, timeout=config.timeout_ms / 1000) as resp:
                body = resp.read().decode("utf-8")
                return self._parse_http_response(body)

        except urllib.error.URLError as e:
            return HookOutput(
                outcome="non_blocking_error",
                continue_=True,
                reason=f"HTTP hook request failed: {e}",
            )
        except Exception as e:
            return HookOutput(
                outcome="non_blocking_error",
                continue_=True,
                reason=f"HTTP hook error: {e}",
            )

    def _parse_http_response(self, body: str) -> HookOutput:
        """解析HTTP响应"""
        import json
        try:
            data = json.loads(body.strip())
            # 处理Python的continue是关键字的问题
            continue_val = data.pop("continue", True) if "continue" in data else True
            return HookOutput(
                outcome="success",
                continue_=continue_val,
                **data
            )
        except json.JSONDecodeError:
            return HookOutput(
                outcome="success",
                continue_=True,
            )


# 全局实例
hooks_manager = HooksManager.get_instance()
