"""
OpenClaw Agent Context System
==============================
Inspired by Claude Code's src/utils/agentContext.ts (178 lines).

核心设计：
- AsyncLocalStorage 隔离并发 Agent 的上下文
- 支持 subagent（Agent 调用 Agent）的嵌套
- 每个 Agent 有独立的 session/request metadata

Claude Code 的设计（TypeScript）：
```typescript
export const agentContext = new AsyncLocalStorage<AgentContext>()
runWithAgentContext(subagentContext, () => runAgent(params))
```

OpenClaw 的 Python 实现：
```python
from openclaw.agent_context import agent_context, run_with_agent_context

ctx = AgentContext(agent_id="123", agent_type="subagent")
result = run_with_agent_context(ctx, lambda: do_work())
```
"""

from __future__ import annotations

import threading
import uuid
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set
from enum import Enum


# ============================================================================
# Agent 上下文类型
# ============================================================================

class AgentType(str, Enum):
    """Agent 类型"""
    MAIN = "main"            # 主 REPL Agent
    SUBAGENT = "subagent"    # 子 Agent（Agent tool 嵌套）
    TEAMMATE = "teammate"    # 团队队友（swarm 模式）


@dataclass
class AgentContext:
    """
    Agent 执行上下文。

    用于在多并发 Agent 环境下隔离各自的元数据。
    类似于 Claude Code 的 SubagentContext 和 TeammateAgentContext。
    """
    # Agent 唯一标识
    agent_id: str = ""
    # 父 Agent 的 session ID（主 Agent 无此字段）
    parent_session_id: Optional[str] = None
    # Agent 类型
    agent_type: AgentType = AgentType.MAIN
    # Agent 名称（用于日志和显示）
    name: Optional[str] = None
    # 团队名称（swarm 模式下使用）
    team_name: Optional[str] = None
    # Agent 配色（UI 显示用）
    color: Optional[str] = None
    # 工具集限制（子集）
    allowed_tools: Optional[Set[str]] = None
    # 权限模式
    permission_mode: str = "default"
    # 是否内置 Agent
    is_builtin: bool = False
    # 创建时间
    created_at: float = field(default_factory=time.time)
    # 请求链追踪
    invoking_request_id: Optional[str] = None
    # 是否已发送首次终端事件（用于遥测）
    invocation_emitted: bool = False
    # 标签（用于分组过滤）
    tags: Set[str] = field(default_factory=set)

    def __post_init__(self):
        if not self.agent_id:
            self.agent_id = str(uuid.uuid4())[:8]

    @property
    def is_subagent(self) -> bool:
        return self.agent_type == AgentType.SUBAGENT

    @property
    def is_main(self) -> bool:
        return self.agent_type == AgentType.MAIN

    @property
    def display_name(self) -> str:
        if self.name:
            return self.name
        if self.team_name:
            return f"{self.name}@{self.team_name}"
        return self.agent_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "parent_session_id": self.parent_session_id,
            "agent_type": self.agent_type.value if isinstance(self.agent_type, Enum) else self.agent_type,
            "name": self.name,
            "team_name": self.team_name,
            "permission_mode": self.permission_mode,
            "is_builtin": self.is_builtin,
            "created_at": self.created_at,
            "allowed_tools": list(self.allowed_tools) if self.allowed_tools else None,
            "tags": list(self.tags),
        }


# ============================================================================
# AsyncLocalStorage 实现
# ============================================================================

# Python 3.11+ 的 ContextVar 等价于 AsyncLocalStorage
# 对于 3.7-3.10，使用 contextvars + threading.local 模拟

import sys
_python_version = sys.version_info[:2]

if _python_version >= (3, 11):
    # Python 3.11+: 原生 ContextVar（支持 async）
    from contextvars import ContextVar

    _current_context: ContextVar[Optional[AgentContext]] = ContextVar(
        'openclaw_agent_context',
        default=None
    )

    def get_current_context() -> Optional[AgentContext]:
        """获取当前 Agent 上下文（无则返回 None）"""
        return _current_context.get()

    def run_with_context(ctx: AgentContext, callable: Callable, *args, **kwargs):
        """在指定上下文中执行函数（支持 async）"""
        token = _current_context.set(ctx)
        try:
            return callable(*args, **kwargs)
        finally:
            _current_context.reset(token)

    # async 版本
    async def run_with_context_async(coro: Callable, *args, **kwargs):
        token = _current_context.set(AgentContext.get())
        try:
            return await coro(*args, **kwargs)
        finally:
            _current_context.reset(token)

else:
    # Python 3.7-3.10: 使用 threading.local 模拟
    # 注意：此版本不支持真正的 async 隔离
    _thread_local = threading.local()

    def get_current_context() -> Optional[AgentContext]:
        return getattr(_thread_local, 'agent_context', None)

    def run_with_context(ctx: AgentContext, callable: Callable, *args, **kwargs):
        old = getattr(_thread_local, 'agent_context', None)
        _thread_local.agent_context = ctx
        try:
            return callable(*args, **kwargs)
        finally:
            if old is None:
                delattr(_thread_local, 'agent_context')
            else:
                _thread_local.agent_context = old

    async def run_with_context_async(coro: Callable, *args, **kwargs):
        # 对于旧版本 Python，回退到同步版本
        return await coro(*args, **kwargs)


# ============================================================================
# 全局上下文变量（兼容旧代码）
# ============================================================================

# 主 Agent 的默认上下文
_main_context = AgentContext(agent_id="main", agent_type=AgentType.MAIN, name="蛋蛋")

# 当前活跃上下文（运行时）
_current_context_var = run_with_context


def get_context() -> AgentContext:
    """获取当前上下文，没有则返回主 Agent 上下文"""
    ctx = get_current_context()
    return ctx if ctx is not None else _main_context


def get_or_create_context(
    agent_id: Optional[str] = None,
    agent_type: AgentType = AgentType.MAIN,
    **kwargs
) -> AgentContext:
    """获取当前上下文，或创建新的子 Agent 上下文"""
    existing = get_current_context()
    if existing is not None and agent_type == AgentType.MAIN:
        return existing

    return AgentContext(
        agent_id=agent_id or str(uuid.uuid4())[:8],
        agent_type=agent_type,
        parent_session_id=existing.agent_id if existing else None,
        **kwargs
    )


class AgentContextManager:
    """
    上下文管理器。

    用于 with 语句管理 Agent 上下文生命周期。

    用法:
        ctx = AgentContext(agent_id="sub-1", agent_type=AgentType.SUBAGENT)
        with AgentContextManager(ctx):
            # 这里 get_context() 返回 sub-1
            do_subagent_work()
        # 出来后恢复主 Agent 上下文
    """

    def __init__(self, ctx: Optional[AgentContext] = None, **kwargs):
        if ctx is None:
            ctx = AgentContext(**kwargs) if kwargs else get_or_create_context(**kwargs)
        self.ctx = ctx
        self._old: Optional[AgentContext] = None

    def __enter__(self) -> AgentContext:
        self._old = get_current_context()
        run_with_context(self.ctx, lambda: None)
        return self.ctx

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._old is None:
            # 清除上下文
            run_with_context(AgentContext(), lambda: None)
        else:
            run_with_context(self._old, lambda: None)
        return False


# ============================================================================
# Subagent 管理
# ============================================================================

class SubagentManager:
    """
    子 Agent 管理器。

    管理所有活跃的子 Agent，支持：
    - spawn: 创建子 Agent
    - kill: 终止子 Agent
    - list: 列出所有子 Agent
    - get: 获取指定 Agent

    注意：这只是一个内存中的管理器，实际的 subagent 执行需要配合 sessions_spawn。
    """

    def __init__(self):
        self._agents: Dict[str, AgentContext] = {}
        self._lock = threading.RLock()
        self._seq = 0

    def spawn(
        self,
        agent_type: AgentType = AgentType.SUBAGENT,
        name: Optional[str] = None,
        allowed_tools: Optional[Set[str]] = None,
        **kwargs
    ) -> AgentContext:
        """创建新的子 Agent"""
        with self._lock:
            self._seq += 1
            parent = get_context()
            ctx = AgentContext(
                agent_id=f"{agent_type.value}-{self._seq}",
                agent_type=agent_type,
                name=name,
                parent_session_id=parent.agent_id if parent else None,
                allowed_tools=allowed_tools,
                **kwargs
            )
            self._agents[ctx.agent_id] = ctx
            return ctx

    def kill(self, agent_id: str) -> bool:
        """终止指定 Agent"""
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                return True
            return False

    def get(self, agent_id: str) -> Optional[AgentContext]:
        return self._agents.get(agent_id)

    def list_all(self) -> list:
        return list(self._agents.values())

    def list_subagents(self) -> list:
        return [a for a in self._agents.values() if a.agent_type == AgentType.SUBAGENT]

    def count(self) -> int:
        return len(self._agents)

    def clear(self) -> int:
        """清除所有 Agent（通常在 session 重置时使用）"""
        with self._lock:
            count = len(self._agents)
            self._agents.clear()
            return count


# 全局子 Agent 管理器
subagent_manager = SubagentManager()


# ============================================================================
# 便捷函数
# ============================================================================

def get_current_agent_id() -> str:
    """获取当前 Agent ID"""
    return get_context().agent_id


def get_current_agent_type() -> AgentType:
    """获取当前 Agent 类型"""
    return get_context().agent_type


def is_main_agent() -> bool:
    """是否为主 Agent"""
    return get_context().is_main


def is_subagent() -> bool:
    """是否为子 Agent"""
    return get_context().is_subagent


def require_permission_mode(mode: str) -> bool:
    """检查当前权限模式是否满足要求"""
    ctx = get_context()
    if ctx.permission_mode == "allow":
        return True
    if ctx.permission_mode == "deny":
        return False
    return mode == "default"
