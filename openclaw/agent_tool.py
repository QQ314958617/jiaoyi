"""
OpenClaw Agent Tool - 子Agent嵌套系统
==========================================
Inspired by Claude Code's AgentTool.tsx (1397 lines).

核心设计：
1. buildTool 工厂模式：基于 BaseTool
2. AsyncLocalStorage 上下文：基于 agent_context.py
3. 三种执行模式：sync / async / teammate
4. worktree 隔离：git worktree 实现文件系统隔离
5. 生命周期管理：register → run → complete/kill/fail
6. 流式进度：async iterator + onProgress 回调
7. 自动后台化：超过阈值后自动转后台
8. 工具过滤：AgentDefinition 定义每个Agent的可用工具

执行模式：
- sync: 同步执行，结果直接返回
- async: 后台执行，返回 agentId，可查询进度
- teammate: tmux 进程隔离的团队协作模式
- remote: 远程CCR环境（Claude Code特有，OpenClaw简化版不实现）
- fork: 实验性fork路径，继承父级system prompt

Agent 定义结构（AgentDefinition）：
- agentType: 唯一标识
- name: 显示名称
- description: 描述
- getSystemPrompt(): 获取系统提示词
- tools: 可用工具列表
- disallowedTools: 禁用工具列表
- model: 默认模型
- permissionMode: 权限模式
- background: 是否默认后台运行
- isolation: 隔离模式(worktree)
- requiredMcpServers: 必需的MCP服务器
- color: UI颜色
- memory: 记忆配置
"""

from __future__ import annotations

import asyncio
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Generic
from concurrent.futures import ThreadPoolExecutor, Future
import queue

from openclaw.tools.base import BaseTool, ToolResult, ToolMetadata, ToolCategory
from openclaw.agent_context import run_with_context, get_context


# ============================================================================
# 执行模式
# ============================================================================

class AgentRunMode(str, Enum):
    """Agent执行模式"""
    SYNC = "sync"           # 同步执行，结果直接返回
    ASYNC = "async"         # 后台执行，返回agentId
    TEAMMATE = "teammate"   # tmux进程隔离
    FORK = "fork"           # 实验性fork路径


class AgentStatus(str, Enum):
    """Agent状态"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 运行中
    BACKGROUNDED = "backgrounded"  # 已转入后台
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"       # 失败
    KILLED = "killed"       # 被杀死


# ============================================================================
# Agent 定义
# ============================================================================

@dataclass
class AgentDefinition:
    """
    Agent定义。

    描述一个Agent的类型、名称、可用工具、权限等。
    对应Claude Code的 AgentDefinition 类型。
    """
    agent_type: str                    # 唯一标识
    name: str                         # 显示名称
    description: str = ""             # 描述
    version: str = "1.0"              # 版本
    # 系统提示词生成器
    get_system_prompt: Optional[Callable[["AgentToolContext"], str]] = None
    # 工具配置
    tools: List[str] = field(default_factory=list)      # 可用工具名列表
    disallowed_tools: List[str] = field(default_factory=list)  # 禁用工具名列表
    # 模型配置
    model: Optional[str] = None       # 默认模型
    # 权限配置
    permission_mode: str = "accepted_edits"  # 权限模式
    # 执行配置
    background: bool = False          # 是否默认后台运行
    isolation: Optional[str] = None    # 隔离模式
    required_mcp_servers: List[str] = field(default_factory=list)  # 必需的MCP服务器
    # UI配置
    color: Optional[str] = None        # UI颜色
    # 记忆配置
    memory: Optional[Dict[str, Any]] = None  # 记忆配置
    # 来源
    source: str = "builtin"           # built-in / custom


@dataclass
class AgentToolInput:
    """Agent Tool 输入参数"""
    description: str                  # 简短描述（3-5词）
    prompt: str                      # 任务描述
    subagent_type: Optional[str] = None  # Agent类型
    model: Optional[str] = None      # 模型覆盖
    run_in_background: bool = False  # 后台运行
    name: Optional[str] = None       # 团队内名称（用于SendMessage）
    team_name: Optional[str] = None  # 团队名
    mode: Optional[str] = None       # 权限模式
    isolation: Optional[str] = None  # 隔离模式
    cwd: Optional[str] = None        # 工作目录覆盖


@dataclass
class AgentToolOutput:
    """Agent Tool 输出"""
    status: str                      # completed / async_launched / teammate_spawned / remote_launched
    prompt: str = ""
    agent_id: Optional[str] = None
    description: Optional[str] = None
    output_file: Optional[str] = None
    can_read_output_file: bool = False
    # teammate 特有
    teammate_id: Optional[str] = None
    color: Optional[str] = None
    tmux_session: Optional[str] = None
    team_name: Optional[str] = None


# ============================================================================
# 任务注册表
# ============================================================================

@dataclass
class AgentTask:
    """已注册的Agent任务"""
    task_id: str
    agent_type: str
    description: str
    prompt: str
    status: AgentStatus = AgentStatus.PENDING
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    messages: List[Dict] = field(default_factory=list)
    progress: Dict[str, Any] = field(default_factory=dict)
    # 底层线程/进程
    future: Optional[Future] = None
    abort_event: Optional[threading.Event] = None
    # 工作目录
    worktree_path: Optional[str] = None
    worktree_branch: Optional[str] = None


class AgentRegistry:
    """
    全局Agent注册表。

    管理所有Agent定义和运行中的任务。
    """
    _instance: Optional["AgentRegistry"] = None
    _lock = threading.RLock()

    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}
        self._tasks: Dict[str, AgentTask] = {}
        self._name_registry: Dict[str, str] = {}  # name -> task_id
        self._task_lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "AgentRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ---------------------
    # Agent 定义管理
    # ---------------------

    def register_agent(self, agent_def: AgentDefinition) -> None:
        """注册一个Agent定义"""
        with self._lock:
            self._agents[agent_def.agent_type] = agent_def

    def get_agent(self, agent_type: str) -> Optional[AgentDefinition]:
        """获取Agent定义"""
        with self._lock:
            return self._agents.get(agent_type)

    def list_agents(self) -> List[AgentDefinition]:
        """列出所有Agent定义"""
        with self._lock:
            return list(self._agents.values())

    # ---------------------
    # 任务管理
    # ---------------------

    def register_task(self, task: AgentTask) -> str:
        """注册一个新任务"""
        with self._task_lock:
            self._tasks[task.task_id] = task
            if task.description:
                self._name_registry[task.description] = task.task_id
        return task.task_id

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """获取任务"""
        with self._task_lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务"""
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            return True

    def complete_task(self, task_id: str, result: Any) -> bool:
        """标记任务完成"""
        return self.update_task(
            task_id,
            status=AgentStatus.COMPLETED,
            result=result,
            end_time=time.time()
        )

    def fail_task(self, task_id: str, error: str) -> bool:
        """标记任务失败"""
        return self.update_task(
            task_id,
            status=AgentStatus.FAILED,
            error=error,
            end_time=time.time()
        )

    def kill_task(self, task_id: str) -> bool:
        """杀死任务"""
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.abort_event:
                task.abort_event.set()
            return self.update_task(
                task_id,
                status=AgentStatus.KILLED,
                end_time=time.time()
            )

    def list_tasks(self, status: Optional[AgentStatus] = None) -> List[AgentTask]:
        """列出任务"""
        with self._task_lock:
            if status:
                return [t for t in self._tasks.values() if t.status == status]
            return list(self._tasks.values())

    def get_task_by_name(self, name: str) -> Optional[AgentTask]:
        """通过名称获取任务"""
        with self._task_lock:
            task_id = self._name_registry.get(name)
            if task_id:
                return self._tasks.get(task_id)
        return None

    # ---------------------
    # 工具过滤
    # ---------------------

    def filter_tools_for_agent(
        self,
        agent_type: str,
        available_tools: List[str],
        is_async: bool = False
    ) -> List[str]:
        """
        根据Agent定义过滤可用工具。

        对应 Claude Code 的 filterToolsForAgent()。
        """
        agent = self.get_agent(agent_type)
        if not agent:
            return available_tools

        # MCP工具对所有Agent开放
        result = [t for t in available_tools if t.startswith("mcp__")]

        # 添加Agent定义中的工具
        if agent.tools:
            # 通配符
            if "*" in agent.tools:
                result = available_tools[:]
            else:
                for tool in agent.tools:
                    if tool in available_tools:
                        result.append(tool)

        # 移除禁用工具
        for tool in agent.disallowed_tools:
            if tool in result:
                result.remove(tool)

        # 异步模式下额外过滤
        if is_async:
            async_allowed = {"BashTool", "ReadTool", "WriteTool", "NotebookEditTool",
                           "GrepTool", "WebSearchTool", "WebFetchTool"}
            result = [t for t in result if t in async_allowed or t.startswith("mcp__")]

        return result


# 全局注册表
agent_registry = AgentRegistry.get_instance()


# ============================================================================
# 内置Agent定义
# ============================================================================

GENERAL_PURPOSE_AGENT = AgentDefinition(
    agent_type="general_purpose",
    name="General Purpose Agent",
    description="通用Agent，可以执行各种任务",
    tools=["*"],  # 所有工具
    permission_mode="accepted_edits",
    source="builtin"
)

# 注册内置Agent
agent_registry.register_agent(GENERAL_PURPOSE_AGENT)


# ============================================================================
# Worktree 隔离
# ============================================================================

class WorktreeManager:
    """
    Git Worktree 隔离管理器。

    为Agent创建临时git worktree，实现文件系统隔离。
    """

    def __init__(self):
        self._worktrees: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def create_worktree(self, slug: str, base_path: str = ".") -> Optional[Dict[str, Any]]:
        """
        创建worktree。

        Returns:
            dict: {worktree_path, worktree_branch, head_commit, git_root}
        """
        import subprocess
        import os

        try:
            # 获取git根目录
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, cwd=base_path
            )
            if result.returncode != 0:
                return None
            git_root = result.stdout.strip()

            # 获取当前分支和commit
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, cwd=git_root
            )
            branch = result.stdout.strip() if result.returncode == 0 else "main"

            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, cwd=git_root
            )
            head_commit = result.stdout.strip() if result.returncode == 0 else None

            # 创建worktree目录
            worktree_path = os.path.join(os.path.dirname(git_root), f".worktree-{slug}")
            os.makedirs(worktree_path, exist_ok=True)

            # 创建worktree
            result = subprocess.run(
                ["git", "worktree", "add", "-b", f"worktree-{slug}", worktree_path],
                capture_output=True, text=True, cwd=git_root
            )

            info = {
                "worktree_path": worktree_path,
                "worktree_branch": f"worktree-{slug}",
                "head_commit": head_commit,
                "git_root": git_root
            }

            with self._lock:
                self._worktrees[slug] = info

            return info

        except Exception:
            return None

    def cleanup_worktree(self, slug: str, remove_branch: bool = True) -> bool:
        """清理worktree"""
        import subprocess

        with self._lock:
            info = self._worktrees.get(slug)
            if not info:
                return False

        try:
            # 移除worktree
            subprocess.run(
                ["git", "worktree", "remove", info["worktree_path"]],
                capture_output=True
            )

            # 移除分支
            if remove_branch and info.get("worktree_branch"):
                subprocess.run(
                    ["git", "branch", "-D", info["worktree_branch"]],
                    capture_output=True, cwd=info.get("git_root")
                )

            del self._worktrees[slug]
            return True

        except Exception:
            return False


worktree_manager = WorktreeManager()


# ============================================================================
# 异步Agent生命周期
# ============================================================================

async def run_async_agent_lifecycle(
    task_id: str,
    agent_type: str,
    prompt: str,
    description: str,
    agent_def: AgentDefinition,
    tools: List[str],
    on_progress: Optional[Callable] = None,
    abort_event: Optional[threading.Event] = None,
    worktree_path: Optional[str] = None,
    cwd_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    异步Agent的完整生命周期。

    对应 Claude Code 的 runAsyncAgentLifecycle()。
    包括：
    1. 启动Agent协程
    2. 处理进度更新
    3. 处理完成/失败/杀死
    4. 清理worktree
    """
    from openclaw.hooks import trigger_trade, trigger_error

    registry = AgentRegistry.get_instance()
    start_time = time.time()

    try:
        # 更新状态为运行中
        registry.update_task(task_id, status=AgentStatus.RUNNING)

        # 如果有worktree或cwd覆盖，切换目录
        original_cwd = None
        if worktree_path or cwd_override:
            import os
            original_cwd = os.getcwd()
            target_dir = worktree_path or cwd_override
            if os.path.exists(target_dir):
                os.chdir(target_dir)

        try:
            # 这里调用实际的Agent执行逻辑
            # 在OpenClaw中，这会调用 MiniMax API 或本地模型
            result = await execute_agent(
                agent_type=agent_type,
                prompt=prompt,
                tools=tools,
                agent_def=agent_def,
                on_progress=on_progress,
                abort_event=abort_event
            )

            # 计算执行时间
            duration_ms = (time.time() - start_time) * 1000

            # 标记完成
            registry.complete_task(
                task_id,
                result={
                    "content": result.get("content", ""),
                    "tool_uses": result.get("tool_uses", 0),
                    "duration_ms": duration_ms
                }
            )

            return {
                "status": "completed",
                "result": result,
                "duration_ms": duration_ms
            }

        finally:
            # 恢复原始目录
            if original_cwd:
                import os
                os.chdir(original_cwd)

            # 清理worktree
            if worktree_path:
                # 检查是否有变更
                worktree_manager.cleanup_worktree(task_id[:8])

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = str(e)

        registry.fail_task(task_id, error=error_msg)

        # 触发错误钩子
        trigger_error(Exception(error_msg), {"task_id": task_id, "agent_type": agent_type})

        return {
            "status": "failed",
            "error": error_msg,
            "duration_ms": duration_ms
        }


async def _call_minimax_chat(
    messages: List[Dict[str, str]],
    model: str = "MiniMax-Text-01",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    tools: Optional[List[Dict[str, Any]]] = None,
    timeout: int = 60,
    bot_name: str = "dandan",
    system_prompt: str = "你是蛋蛋，一个幽默搞笑的AI助手",
) -> Dict[str, Any]:
    """
    调用 MiniMax Chat API。

    对应 Claude Code 中 AI 模型的实际调用。
    支持 tool use（函数调用）。

    MiniMax 特有参数：
    - bot_setting: 机器人配置（name + prompt）
    - reply_constraints: 回复约束（sender_type=BOT, sender_name=bot_name）
    - messages 中每条需要 sender_name + sender_type=USER
    """
    import os
    import json
    import urllib.request
    import urllib.error

    api_key = os.environ.get("MINIMAX_API_KEY", "")
    if not api_key:
        return {"error": "MINIMAX_API_KEY not set", "choices": []}

    # 转换 messages 格式（MiniMax 需要 sender_name + sender_type）
    mm_messages = []
    for msg in messages:
        role = msg.get("role", "user")
        if role == "system":
            # system prompt 通过 bot_setting 传入，不作为单独 message
            continue
        sender_type = "USER" if role in ("user", "human") else "BOT"
        mm_messages.append({
            "role": role,
            "sender_name": msg.get("sender_name", "user" if sender_type == "USER" else bot_name),
            "sender_type": sender_type,
            "content": msg.get("content", "")
        })

    url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": model if model != "MiniMax-Text-01" else "abab6.5s-chat",
        "messages": mm_messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "bot_setting": [{
            "bot_name": bot_name,
            "content": system_prompt,
        }],
        "reply_constraints": {
            "rich_text": True,
            "sender_type": "BOT",
            "sender_name": bot_name,
        },
    }

    if tools:
        data["tools"] = tools

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        start_time = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        duration_ms = int((time.time() - start_time) * 1000)

        # 追踪成本
        try:
            from openclaw.cost_tracker import record_api_call
            usage = result.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", len(str(messages)) * 4)  # 估算
            output_tokens = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)
            record_api_call(
                model=model if model != "MiniMax-Text-01" else "abab6.5s-chat",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
                success=True,
            )
        except Exception:
            pass  # 成本追踪失败不影响主流程

        # 标准化返回格式
        reply = result.get("reply", "")
        if reply:
            return {
                "choices": [{"message": {"content": reply}}],
                "model": result.get("model", model),
                "usage": {"total_tokens": result.get("usage_tokens", 0)},
            }
        elif result.get("base_resp", {}).get("status_code") == 1008:
            return {"error": "insufficient balance", "choices": [], "base_resp": result.get("base_resp")}
        elif result.get("base_resp", {}).get("status_code", 0) != 0:
            return {"error": result.get("base_resp", {}).get("status_msg", "unknown error"), "choices": []}

        return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return {"error": f"HTTP {e.code}: {error_body}", "choices": []}
    except Exception as e:
        return {"error": str(e), "choices": []}


async def call_agent(
    agent_type: str,
    prompt: str,
    tools: List[str],
    agent_def: AgentDefinition,
    on_progress: Optional[Callable] = None,
    abort_event: Optional[threading.Event] = None,
) -> Dict[str, Any]:
    """
    执行Agent的实际逻辑。

    这是OpenClaw中调用AI模型的核心函数。
    在Claude Code中，这会调用 runAgent() 生成器。
    """
    from openclaw.hooks import trigger_trade

    # 获取Agent的系统提示词
    system_prompt = ""
    if agent_def.get_system_prompt:
        ctx = AgentToolContext(
            task_id="",
            agent_type=agent_type,
            tools=tools,
            permission_mode=agent_def.permission_mode
        )
        system_prompt = agent_def.get_system_prompt(ctx)

    # 触发交易钩子（如果有相关操作）
    trigger_trade(
        action="agent_start",
        stock_code="",
        shares=0,
        result={"agent_type": agent_type, "prompt": prompt}
    )

    # 构建消息
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # 调用 MiniMax API
    result = await _call_minimax_chat(
        messages=messages,
        model=agent_def.model or "MiniMax-Text-01",
        max_tokens=4096,
        temperature=0.7,
    )

    if "error" in result:
        return {
            "content": f"[Agent调用失败] {result['error']}",
            "tool_uses": 0,
            "error": result["error"]
        }

    # 解析响应
    choices = result.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        content = message.get("content", "")

        # 检查是否有 tool_calls
        tool_calls = message.get("tool_calls", [])
        if tool_calls:
            return {
                "content": content,
                "tool_uses": len(tool_calls),
                "tool_calls": tool_calls,
                "model": result.get("model", ""),
                "usage": result.get("usage", {}),
            }

        return {
            "content": content,
            "tool_uses": 0,
            "model": result.get("model", ""),
            "usage": result.get("usage", {}),
        }

    return {
        "content": "[Agent响应为空]",
        "tool_uses": 0
    }


# ============================================================================
# 流式Agent执行（第2轮深化）
# ============================================================================

from dataclasses import dataclass
from typing import AsyncIterator, Optional, Dict, Any, List, Callable
import json


@dataclass
class AgentStreamEvent:
    """
    Agent流式事件。

    对应 Claude Code 的 Message 类型。
    """
    type: str  # "message" / "tool_use" / "tool_result" / "complete" / "error"
    content: str = ""
    tool_name: str = ""
    tool_args: Optional[Dict] = None
    tool_result: Any = None
    model: str = ""
    done: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


async def stream_agent(
    agent_type: str,
    prompt: str,
    tools: List[str],
    agent_def: AgentDefinition,
    on_progress: Optional[Callable[[AgentStreamEvent], None]] = None,
    abort_event: Optional[threading.Event] = None,
) -> AsyncIterator[AgentStreamEvent]:
    """
    流式执行Agent。

    对应 Claude Code 的 runAgent() AsyncGenerator<Message>。

    使用方式：
        async for event in stream_agent(...):
            if event.type == "message":
                print(event.content, end="", flush=True)
            elif event.type == "tool_use":
                print(f"\\n[Calling {event.tool_name}]")

    Yields:
        AgentStreamEvent - 流式事件序列
    """
    from openclaw.hooks import trigger_trade

    # 1. 触发开始事件
    yield AgentStreamEvent(
        type="message",
        content=f"[Agent {agent_type} 开始执行...]",
        metadata={"phase": "start", "agent_type": agent_type}
    )

    # 2. 获取系统提示词
    system_prompt = ""
    if agent_def.get_system_prompt:
        ctx = AgentToolContext(
            task_id="",
            agent_type=agent_type,
            tools=tools,
            permission_mode=agent_def.permission_mode
        )
        system_prompt = agent_def.get_system_prompt(ctx)

    # 3. 触发交易钩子
    trigger_trade(
        action="agent_start",
        stock_code="",
        shares=0,
        result={"agent_type": agent_type, "prompt": prompt}
    )

    # 4. 构建消息
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # 5. 调用模型（分块yield）
    result = await _call_minimax_chat(
        messages=messages,
        model=agent_def.model or "MiniMax-Text-01",
        max_tokens=4096,
        temperature=0.7,
    )

    if "error" in result:
        yield AgentStreamEvent(
            type="error",
            content=f"[Agent调用失败] {result['error']}",
            metadata={"phase": "error", "error": result["error"]}
        )
        return

    # 6. 解析响应
    choices = result.get("choices", [])
    if not choices:
        yield AgentStreamEvent(
            type="complete",
            content="[Agent响应为空]",
            done=True,
        )
        return

    message = choices[0].get("message", {})
    content = message.get("content", "")
    tool_calls = message.get("tool_calls", [])

    # 7. 先yield内容
    if content:
        yield AgentStreamEvent(
            type="message",
            content=content,
            model=result.get("model", ""),
        )

    # 8. 然后yield tool_calls（如果有）
    for tc in tool_calls:
        func = tc.get("function", {})
        tool_name = func.get("name", "")
        tool_args = func.get("arguments", {})

        # 解析 arguments（可能是 JSON string）
        if isinstance(tool_args, str):
            try:
                tool_args = json.loads(tool_args)
            except json.JSONDecodeError:
                tool_args = {"raw": tool_args}

        yield AgentStreamEvent(
            type="tool_use",
            content=f"[调用工具: {tool_name}]",
            tool_name=tool_name,
            tool_args=tool_args,
        )

        # 触发 tool_use 回调
        if on_progress:
            on_progress(AgentStreamEvent(
                type="tool_use",
                tool_name=tool_name,
                tool_args=tool_args,
            ))

        # TODO: 实际执行工具并yield结果
        # 这里需要集成 ToolRegistry 来真正执行工具
        yield AgentStreamEvent(
            type="tool_result",
            tool_name=tool_name,
            tool_result={"status": "pending", "note": "工具执行需要集成ToolRegistry"},
        )

    # 9. 完成
    yield AgentStreamEvent(
        type="complete",
        content=content,
        done=True,
        metadata={
            "tool_uses": len(tool_calls),
            "model": result.get("model", ""),
            "usage": result.get("usage", {}),
        }
    )


# ============================================================================
# AgentTool
# ============================================================================

@dataclass
class AgentToolContext:
    """传递给Agent工具的上下文"""
    task_id: str
    agent_type: str
    tools: List[str]
    permission_mode: str
    abort_event: Optional[threading.Event] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentTool(BaseTool):
    """
    Agent嵌套工具。

    对应 Claude Code 的 AgentTool.tsx。
    允许主Agent spawn子Agent来执行任务。

    输入参数：
    - description: 简短描述（3-5词）
    - prompt: 任务描述
    - subagent_type: Agent类型（默认general_purpose）
    - model: 模型覆盖
    - run_in_background: 是否后台运行
    - name: 团队内名称（用于SendMessage路由）
    - team_name: 团队名
    - isolation: 隔离模式（worktree）
    - cwd: 工作目录覆盖

    输出：
    - status: completed / async_launched / teammate_spawned
    - agent_id: 任务ID
    - description: 任务描述
    - output_file: 输出文件路径
    """

    name = "Agent"
    description = "Launch a new agent to perform a task"
    category = ToolCategory.SYSTEM
    tags = {"agent", "delegate", "subagent", "spawn"}
    version = "1.0.0"

    def __init__(self):
        super().__init__()
        self._registry = None

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description=self.description,
            category=self.category,
            tags=self.tags,
            version=self.version,
        )

    async def call(self, ctx: Any, input_data: Dict[str, Any]) -> ToolResult:
        """
        执行Agent嵌套。

        对应 Claude Code AgentTool.call()。
        """
        registry = AgentRegistry.get_instance()
        start_time = time.time()

        # 解析Agent类型
        effective_type = input_data.get("subagent_type") or "general_purpose"
        agent_def = registry.get_agent(effective_type)

        if not agent_def:
            return ToolResult(
                success=False,
                error=f"Agent type '{effective_type}' not found. Available: {registry.list_agents()}"
            )

        # 检查团队功能（简化版暂不支持）
        if input_data.get("team_name"):
            return ToolResult(
                success=False,
                error="Team mode is not yet supported in this version."
            )

        # 解析执行模式
        should_async = (
            input_data.get("run_in_background") or
            agent_def.background or
            effective_type == "fork"  # fork路径强制async
        )

        # 创建abort事件
        abort_event = threading.Event()

        # 如果需要worktree隔离
        worktree_info = None
        if input_data.get("isolation") == "worktree":
            slug = f"agent-{uuid.uuid4().hex[:8]}"
            worktree_info = worktree_manager.create_worktree(slug)
            if not worktree_info:
                return ToolResult(
                    success=False,
                    error="Failed to create worktree for isolation"
                )

        # 创建任务
        task_id = str(uuid.uuid4())
        task = AgentTask(
            task_id=task_id,
            agent_type=effective_type,
            description=input_data.get("description"),
            prompt=input_data.get("prompt"),
            abort_event=abort_event,
            worktree_path=worktree_info.get("worktree_path") if worktree_info else None,
            worktree_branch=worktree_info.get("worktree_branch") if worktree_info else None
        )

        # 过滤工具
        available_tools = registry.filter_tools_for_agent(
            effective_type,
            input_data.get("tools", []),
            is_async=should_async
        )

        # 注册任务
        registry.register_task(task)

        # 获取执行循环的上下文
        parent_ctx = get_context()
        parent_session_id = parent_ctx.session_id if parent_ctx else None

        # 设置Agent上下文
        agent_ctx = {
            "agent_id": task_id,
            "parent_session_id": parent_session_id,
            "agent_type": "subagent",
            "subagent_name": effective_type,
            "is_builtin": agent_def.source == "builtin",
            "invocation_kind": "spawn",
        }

        if should_async:
            # 异步模式：立即返回agent_id
            def run_background():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        run_with_context(
                            agent_ctx,
                            run_async_agent_lifecycle(
                                task_id=task_id,
                                agent_type=effective_type,
                                prompt=input_data.get("prompt"),
                                description=input_data.get("description"),
                                agent_def=agent_def,
                                tools=available_tools,
                                abort_event=abort_event,
                                worktree_path=worktree_info.get("worktree_path") if worktree_info else None,
                                cwd_override=input_data.get("cwd")
                            )
                        )
                    )
                finally:
                    loop.close()

            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(run_background)
            task.future = future
            executor.shutdown(wait=False)

            return ToolResult(
                success=True,
                data=AgentToolOutput(
                    status="async_launched",
                    agent_id=task_id,
                    description=input_data.get("description"),
                    prompt=input_data.get("prompt"),
                    output_file=f"/tmp/agent_output_{task_id}.json",
                    can_read_output_file=True
                ).__dict__
            )
        else:
            # 同步模式：等待结果
            result = await run_with_context(
                agent_ctx,
                run_async_agent_lifecycle(
                    task_id=task_id,
                    agent_type=effective_type,
                    prompt=input_data.get("prompt"),
                    description=input_data.get("description"),
                    agent_def=agent_def,
                    tools=available_tools,
                    abort_event=abort_event,
                    worktree_path=worktree_info.get("worktree_path") if worktree_info else None,
                    cwd_override=input_data.get("cwd")
                )
            )

            return ToolResult(
                success=True,
                data=AgentToolOutput(
                    status="completed",
                    agent_id=task_id,
                    description=input_data.get("description"),
                    prompt=input_data.get("prompt")
                ).__dict__
            )


# 创建单例
agent_tool = AgentTool()


# ============================================================================
# 内省工具
# ============================================================================

class ListAgentsTool(BaseTool):
    """列出所有可用的Agent定义"""

    name = "ListAgents"
    description = "List all available agent types"
    category = ToolCategory.SYSTEM
    tags = {"agent", "list", "metadata"}
    version = "1.0.0"

    async def call(self, input: Dict[str, Any], context: Any = None) -> ToolResult:
        registry = AgentRegistry.get_instance()
        agents = registry.list_agents()

        return ToolResult(
            success=True,
            data={
                "agents": [
                    {
                        "type": a.agent_type,
                        "name": a.name,
                        "description": a.description,
                        "tools_count": len(a.tools),
                        "source": a.source
                    }
                    for a in agents
                ]
            }
        )


class GetTaskTool(BaseTool):
    """获取Agent任务状态"""

    name = "GetTask"
    description = "Get the status of an agent task"
    category = ToolCategory.SYSTEM
    tags = {"agent", "task", "status"}
    version = "1.0.0"

    async def call(self, input: Dict[str, Any], context: Any = None) -> ToolResult:
        task_id = input.get("task_id")
        if not task_id:
            return ToolResult(success=False, error="task_id is required")

        registry = AgentRegistry.get_instance()
        task = registry.get_task(task_id)

        if not task:
            return ToolResult(success=False, error=f"Task {task_id} not found")

        return ToolResult(
            success=True,
            data={
                "task_id": task.task_id,
                "status": task.status.value,
                "description": task.description,
                "progress": task.progress,
                "result": task.result,
                "error": task.error
            }
        )


class KillAgentTool(BaseTool):
    """杀死运行中的Agent任务"""

    name = "KillAgent"
    description = "Kill a running agent task"
    category = ToolCategory.SYSTEM
    tags = {"agent", "task", "kill"}
    version = "1.0.0"

    async def call(self, input: Dict[str, Any], context: Any = None) -> ToolResult:
        task_id = input.get("task_id")
        if not task_id:
            return ToolResult(success=False, error="task_id is required")

        registry = AgentRegistry.get_instance()
        success = registry.kill_task(task_id)

        if success:
            return ToolResult(success=True, data={"message": f"Task {task_id} killed"})
        else:
            return ToolResult(success=False, error=f"Failed to kill task {task_id}")


# ============================================================================
# 便捷函数
# ============================================================================

def spawn_agent(
    agent_type: str,
    prompt: str,
    description: str,
    run_async: bool = True,
    **kwargs
) -> AgentToolOutput:
    """
    快速spawn一个Agent。

    用法：
        result = spawn_agent(
            agent_type="general_purpose",
            prompt="分析今天的交易记录",
            description="分析交易"
        )
    """
    input_obj = AgentToolInput(
        description=description,
        prompt=prompt,
        subagent_type=agent_type,
        run_in_background=run_async,
        **kwargs
    )

    tool = AgentTool()
    result = asyncio.get_event_loop().run_until_complete(
        tool.execute(input_obj)
    )

    if result.success:
        return AgentToolOutput(**result.data)
    else:
        raise Exception(result.error)


# ============================================================================
# Async Stream（第15个模块 - streaming utility）
# ============================================================================

import asyncio
from typing import AsyncIterator, AsyncIterable, TypeVar, Optional, Callable, Awaitable

T = TypeVar("T")


class Stream(AsyncIterator[T]):
    """
    Async 流式迭代器。

    对应 Claude Code 的 src/utils/stream.ts (76行)。
    基于 queue + Promise 的 async iterator 实现。

    用法：
        stream = Stream()
        async for item in stream:
            print(item)
        # 或者
        async def producer():
            stream.enqueue(item)
            stream.done()
    """

    def __init__(self, on_return: Optional[Callable[[], Awaitable[None]]] = None):
        self._queue: list[T] = []
        self._read_resolve: Optional[Callable[[T], None]] = None
        self._read_reject: Optional[Callable[[Exception], None]] = None
        self._is_done = False
        self._has_error: Optional[Exception] = None
        self._started = False
        self._on_return = on_return

    def __aiter__(self) -> AsyncIterator[T]:
        if self._started:
            raise RuntimeError("Stream can only be iterated once")
        self._started = True
        return self

    async def __anext__(self) -> T:
        if self._queue:
            return self._queue.pop(0)

        if self._is_done:
            raise StopAsyncIteration

        if self._has_error:
            raise self._has_error

        # Wait for enqueue() to be called
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def resolve(value: T):
            if not future.done():
                future.set_result(value)

        self._read_resolve = resolve
        self._read_reject = lambda e: future.set_exception(e) if not future.done() else None

        return await future

    def enqueue(self, value: T) -> None:
        """加入一个值到流"""
        if self._read_resolve:
            resolve = self._read_resolve
            self._read_resolve = None
            self._read_reject = None
            resolve(value)
        else:
            self._queue.append(value)

    def done(self) -> None:
        """标记流结束"""
        self._is_done = True
        if self._read_resolve:
            resolve = self._read_resolve
            self._read_resolve = None
            self._read_reject = None
            resolve(None)  # type: ignore

    def error(self, exc: Exception) -> None:
        """标记流出错"""
        self._has_error = exc
        if self._read_reject:
            reject = self._read_reject
            self._read_resolve = None
            self._read_reject = None
            reject(exc)

    async def aclose(self) -> None:
        """异步关闭流"""
        self._is_done = True
        if self._on_return:
            await self._on_return()


def stream_from_async_gen(
    gen: AsyncIterator[T]
) -> Stream[T]:
    """
    将 async generator 转换为 Stream。

    对应 Claude Code 中 runAgent() 的流式输出模式。
    """
    stream = Stream[T]()

    async def consume():
        try:
            async for item in gen:
                stream.enqueue(item)
            stream.done()
        except Exception as e:
            stream.error(e)

    asyncio.create_task(consume())
    return stream
