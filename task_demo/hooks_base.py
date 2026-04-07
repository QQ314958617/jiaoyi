"""
Hooks System - 事件钩子系统
从 Claude Code src/utils/hooks.ts 移植（精简版）

核心概念：
1. HookEvent - 事件类型（PreToolUse, PostToolUse, SessionStart等）
2. HookConfig - 钩子配置（命令/函数 + 匹配条件）
3. HookExecutor - 钩子执行器（超时/中止/结果处理）
4. SessionHookRegistry - 会话级钩子注册表

用途：
- 定时任务触发（cron钩子）
- 工具执行前后处理
- 会话开始/结束处理
- 文件变更监听
"""
import os
import re
import subprocess
import threading
import time
import json
import asyncio
from enum import Enum
from typing import Callable, Dict, List, Optional, Any, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod


# ============================================================================
# Hook Events - 事件类型枚举
# ============================================================================

class HookEvent(str, Enum):
    """支持的钩子事件类型"""
    # 工具相关
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    POST_TOOL_USE_FAILURE = "PostToolUseFailure"

    # 会话相关
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    SETUP = "Setup"

    # 停止相关
    STOP = "Stop"
    STOP_FAILURE = "StopFailure"

    # 子代理相关
    SUBAGENT_START = "SubagentStart"
    SUBAGENT_STOP = "SubagentStop"

    # 压缩相关
    PRE_COMPACT = "PreCompact"
    POST_COMPACT = "PostCompact"

    # 权限相关
    PERMISSION_REQUEST = "PermissionRequest"
    PERMISSION_DENIED = "PermissionDenied"

    # 团队相关
    TEAMMATE_IDLE = "TeammateIdle"

    # 任务相关
    TASK_CREATED = "TaskCreated"
    TASK_COMPLETED = "TaskCompleted"

    # 提示相关
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    NOTIFICATION = "Notification"

    # 采集请求
    ELICITATION = "Elicitation"
    ELICITATION_RESULT = "ElicitationResult"

    # 配置相关
    CONFIG_CHANGE = "ConfigChange"

    # 工作目录相关
    WORKTREE_CREATE = "WorktreeCreate"
    WORKTREE_REMOVE = "WorktreeRemove"
    INSTRUCTIONS_LOADED = "InstructionsLoaded"
    CWD_CHANGED = "CwdChanged"
    FILE_CHANGED = "FileChanged"


# 常用事件别名（便于使用）
HOOK_EVENTS = list(HookEvent)


# ============================================================================
# Hook Types - 钩子类型
# ============================================================================

class HookType(str, Enum):
    """钩子执行类型"""
    COMMAND = "command"      # Shell命令
    FUNCTION = "function"    # Python回调函数
    HTTP = "http"           # HTTP请求


# ============================================================================
# Hook Input - 传递给钩子的输入
# ============================================================================

@dataclass
class HookInput:
    """传递给钩子的上下文信息"""
    hook_event_name: HookEvent
    session_id: str
    cwd: str
    transcript_path: str = ""
    permission_mode: Optional[str] = None
    agent_id: Optional[str] = None
    agent_type: Optional[str] = None

    # 工具相关字段
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_use_id: Optional[str] = None

    # 额外数据
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hook_event_name": self.hook_event_name.value if isinstance(self.hook_event_name, HookEvent) else self.hook_event_name,
            "session_id": self.session_id,
            "cwd": self.cwd,
            "transcript_path": self.transcript_path,
            "permission_mode": self.permission_mode,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_use_id": self.tool_use_id,
            **self.extra,
        }


# ============================================================================
# Hook Output - 钩子输出的JSON Schema
# ============================================================================

@dataclass
class HookOutput:
    """钩子执行结果"""
    outcome: str = "success"  # success | blocking | non_blocking_error | cancelled
    continue_: bool = True     # 是否继续执行
    suppress_output: bool = False
    stop_reason: Optional[str] = None
    decision: Optional[str] = None  # approve | block
    reason: Optional[str] = None
    system_message: Optional[str] = None

    # 工具相关
    permission_decision: Optional[str] = None  # allow | deny | ask
    permission_decision_reason: Optional[str] = None
    updated_input: Optional[Dict[str, Any]] = None
    additional_context: Optional[str] = None

    # 提示相关
    initial_user_message: Optional[str] = None
    watch_paths: Optional[List[str]] = None
    retry: bool = False

    # 错误相关
    blocking_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "continue": self.continue_,
            "suppressOutput": self.suppress_output,
            "outcome": self.outcome,
        }
        if self.stop_reason:
            result["stopReason"] = self.stop_reason
        if self.decision:
            result["decision"] = self.decision
        if self.reason:
            result["reason"] = self.reason
        if self.system_message:
            result["systemMessage"] = self.system_message
        if self.permission_decision:
            result["permissionDecision"] = self.permission_decision
        if self.permission_decision_reason:
            result["permissionDecisionReason"] = self.permission_decision_reason
        if self.updated_input:
            result["updatedInput"] = self.updated_input
        if self.additional_context:
            result["additionalContext"] = self.additional_context
        if self.initial_user_message:
            result["initialUserMessage"] = self.initial_user_message
        if self.watch_paths:
            result["watchPaths"] = self.watch_paths
        if self.retry:
            result["retry"] = self.retry
        if self.blocking_error:
            result["blockingError"] = self.blocking_error
        return result


# ============================================================================
# Hook Configuration - 钩子配置
# ============================================================================

@dataclass
class HookConfig:
    """单个钩子的配置"""
    id: str
    name: str
    hook_type: HookType
    event: HookEvent
    matcher: str = "*"  # 匹配条件，* 表示全部
    enabled: bool = True
    timeout_ms: int = 60000  # 默认60秒超时

    # 命令类型钩子
    command: Optional[str] = None
    shell: Optional[str] = None

    # 函数类型钩子
    callback: Optional[Callable[..., Any]] = None

    # HTTP类型钩子
    url: Optional[str] = None
    method: str = "POST"

    def should_fire(self, context: HookInput) -> bool:
        """判断钩子是否应该触发"""
        if not self.enabled:
            return False

        # 通配符匹配
        if self.matcher == "*":
            return True

        # 工具名匹配
        if context.tool_name:
            return self._match_pattern(self.matcher, context.tool_name)

        return True

    def _match_pattern(self, pattern: str, value: str) -> bool:
        """简单模式匹配（支持*通配符）"""
        if pattern == "*":
            return True
        regex = "^" + pattern.replace("*", ".*") + "$"
        return bool(re.match(regex, value))


# ============================================================================
# Hook Executor - 钩子执行器
# ============================================================================

class HookExecutor:
    """
    钩子执行器
    负责：超时控制 | 中止信号 | 结果解析 | 错误处理
    """

    def __init__(self, timeout_ms: int = 60000):
        self.timeout_ms = timeout_ms
        self._active_processes: Dict[str, subprocess.Popen] = {}

    def execute_command(
        self,
        config: HookConfig,
        hook_input: HookInput,
        abort_event: Optional[threading.Event] = None,
    ) -> HookOutput:
        """
        执行命令类型钩子
        """
        if not config.command:
            return HookOutput(
                outcome="non_blocking_error",
                continue_=True,
                reason="No command configured",
            )

        # 构建环境变量
        env = os.environ.copy()
        env["HOOK_EVENT"] = config.event.value
        env["HOOK_SESSION_ID"] = hook_input.session_id
        env["HOOK_CWD"] = hook_input.cwd
        if hook_input.tool_name:
            env["HOOK_TOOL_NAME"] = hook_input.tool_name

        # 构建命令（支持输入作为JSON）
        input_json = json.dumps(hook_input.to_dict())
        full_command = f'echo \'{input_json}\' | {config.command}'

        try:
            process = subprocess.Popen(
                full_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            self._active_processes[config.id] = process

            # 等待完成（带超时）
            timeout_sec = config.timeout_ms / 1000
            try:
                stdout, stderr = process.communicate(timeout=timeout_sec)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                return HookOutput(
                    outcome="non_blocking_error",
                    continue_=True,
                    reason=f"Hook timed out after {timeout_sec}s",
                )
            finally:
                self._active_processes.pop(config.id, None)

            # 解析输出
            return self._parse_output(stdout, stderr, exit_code)

        except Exception as e:
            return HookOutput(
                outcome="non_blocking_error",
                continue_=True,
                reason=f"Hook execution failed: {e}",
            )

    def execute_function(
        self,
        config: HookConfig,
        hook_input: HookInput,
    ) -> HookOutput:
        """
        执行函数类型钩子
        """
        if not config.callback:
            return HookOutput(
                outcome="non_blocking_error",
                continue_=True,
                reason="No callback configured",
            )

        try:
            result = config.callback(hook_input)
            if asyncio.iscoroutine(result):
                # 异步函数
                result = asyncio.run(result)

            if isinstance(result, bool):
                return HookOutput(
                    outcome="success",
                    continue_=result,
                )
            elif isinstance(result, dict):
                # 处理Python的continue是关键字的问题
                if "continue" in result:
                    result["continue_"] = result.pop("continue")
                return HookOutput(**result)
            else:
                return HookOutput(
                    outcome="success",
                    continue_=True,
                )

        except Exception as e:
            return HookOutput(
                outcome="non_blocking_error",
                continue_=True,
                reason=f"Hook callback failed: {e}",
            )

    def _parse_output(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
    ) -> HookOutput:
        """解析钩子输出"""
        trimmed = stdout.strip()

        # 尝试解析JSON
        if trimmed.startswith("{"):
            try:
                data = json.loads(trimmed)
                # 处理Python的continue是关键字的问题
                continue_val = data.pop("continue", True) if "continue" in data else True
                return HookOutput(
                    outcome="success" if exit_code == 0 else "non_blocking_error",
                    continue_=continue_val,
                    **data
                )
            except json.JSONDecodeError:
                pass

        # 非JSON输出
        if exit_code == 0:
            return HookOutput(
                outcome="success",
                continue_=True,
            )
        elif exit_code == 2:
            # 阻塞错误
            return HookOutput(
                outcome="blocking",
                continue_=False,
                blocking_error=stderr or stdout,
            )
        else:
            return HookOutput(
                outcome="non_blocking_error",
                continue_=True,
                reason=f"Exit code {exit_code}: {stderr or stdout}",
            )

    def abort_all(self) -> None:
        """中止所有运行中的钩子"""
        for process in self._active_processes.values():
            try:
                process.terminate()
                time.sleep(0.1)
                if process.poll() is None:
                    process.kill()
            except Exception:
                pass
        self._active_processes.clear()
