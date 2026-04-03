"""
OpenClaw Tool Base System
===========================
Inspired by Claude Code's Tool.ts buildTool architecture.

核心设计：
1. BaseTool 抽象基类 - 所有工具的父类
2. 每个工具定义：名称、描述、输入schema、执行逻辑
3. ToolRegistry 统一管理工具的注册和发现
4. PermissionRule 权限规则引擎

Claude Code 的工具核心接口：
- name: str
- inputSchema: Zod schema
- outputSchema: Zod schema
- call(): 执行工具
- description(): 生成 AI 描述
- prompt(): 生成系统提示词片段
- isEnabled(): 是否启用
- isReadOnly(): 是否只读
- isDestructive(): 是否有破坏性
- validateInput(): 验证输入
- checkPermissions(): 权限检查
"""

from __future__ import annotations

import json
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Generic
from enum import Enum
import asyncio

# ============================================================================
# 工具元信息
# ============================================================================

@dataclass
class ToolMetadata:
    """工具元信息"""
    name: str
    description: str
    category: str = "general"          # trading/market/system/general
    tags: Set[str] = field(default_factory=set)
    version: str = "1.0.0"
    author: str = ""
    is_critical: bool = False          # 关键工具
    aliases: List[str] = field(default_factory=list)  # 别名，支持重命名兼容

    def to_dict(self) -> Dict:
        return asdict(self)


class ToolCategory(str, Enum):
    """工具分类"""
    TRADING = "trading"       # 交易相关
    MARKET = "market"        # 市场数据
    REVIEW = "review"        # 复盘相关
    SYSTEM = "system"        # 系统工具
    SKILL = "skill"          # Skill执行
    GENERAL = "general"      # 通用


class ToolResultStatus(str, Enum):
    """工具执行结果状态"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"      # 部分成功
    DENIED = "denied"        # 权限拒绝
    VALIDATION_ERROR = "validation_error"


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status: ToolResultStatus = ToolResultStatus.SUCCESS
    execution_time_ms: float = 0.0
    cached: bool = False
    # 用于 AI 理解的简短描述
    summary: Optional[str] = None
    # 是否需要用户交互
    requires_interaction: bool = False
    # 破坏性操作标记
    is_destructive: bool = False

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "cached": self.cached,
            "summary": self.summary,
            "requires_interaction": self.requires_interaction,
            "is_destructive": self.is_destructive,
        }

    @classmethod
    def success_result(cls, data: Any = None, summary: Optional[str] = None, **kwargs) -> "ToolResult":
        return cls(success=True, data=data, status=ToolResultStatus.SUCCESS, summary=summary, **kwargs)

    @classmethod
    def error_result(cls, error: str, data: Any = None, **kwargs) -> "ToolResult":
        return cls(success=False, error=error, data=data, status=ToolResultStatus.ERROR, **kwargs)

    @classmethod
    def denied_result(cls, reason: str = "Permission denied") -> "ToolResult":
        return cls(success=False, error=reason, status=ToolResultStatus.DENIED, requires_interaction=True)


@dataclass
class ToolInput:
    """工具输入参数"""
    raw_input: Dict[str, Any]
    validated: bool = False

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw_input.get(key, default)


@dataclass
class ToolContext:
    """
    工具执行上下文。

    包含工具执行时需要的全部环境信息。
    类似于 Claude Code 的 ToolUseContext。
    """
    session_id: str = ""
    user_id: str = ""
    request_id: str = ""            # 当前请求ID，用于日志追踪
    agent_id: Optional[str] = None  # 当前Agent ID（Agent嵌套时）
    agent_type: str = "main"        # main/subagent/teammate
    permission_mode: str = "default"  # default/ask/allow/deny
    tools: Optional["ToolRegistry"] = None  # 工具注册表引用
    cwd: str = "/root"
    env: Dict[str, str] = field(default_factory=dict)
    # 时间信息
    timestamp: float = field(default_factory=time.time)
    # 统计
    execution_count: int = 0        # 累计执行次数

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "permission_mode": self.permission_mode,
            "cwd": self.cwd,
            "timestamp": self.timestamp,
        }


# ============================================================================
# 权限相关类型
# ============================================================================

class PermissionMode(str, Enum):
    """权限模式"""
    DEFAULT = "default"    # 按规则决策
    ASK = "ask"            # 总是询问
    ALLOW = "allow"        # 总是允许
    DENY = "deny"          # 总是拒绝


class PermissionBehavior(str, Enum):
    """权限行为"""
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass
class PermissionRule:
    """
    权限规则。

    类似于 Claude Code 的 PermissionRule。
    用于控制工具的使用权限。
    """
    tool_name: str
    rule_content: Optional[str] = None   # 如 "git *"（空=全部）
    behavior: PermissionBehavior = PermissionBehavior.ALLOW
    source: str = "user"               # user/plugin/managed/system
    description: str = ""               # 规则描述
    enabled: bool = True

    def matches(self, tool_name: str, input_data: Optional[Dict] = None) -> bool:
        """检查输入是否匹配此规则"""
        if not self.enabled:
            return False
        if self.tool_name != tool_name and self.tool_name != "*":
            return False
        if self.rule_content is None:
            return True  # 通用规则
        # 支持简单的通配符匹配（后续可扩展更复杂的模式）
        import fnmatch
        if input_data:
            input_str = json.dumps(input_data, sort_keys=True)
            if fnmatch.fnmatch(input_str, self.rule_content):
                return True
        return False

    def to_dict(self) -> Dict:
        return {
            "tool_name": self.tool_name,
            "rule_content": self.rule_content,
            "behavior": self.behavior.value if isinstance(self.behavior, Enum) else self.behavior,
            "source": self.source,
            "description": self.description,
            "enabled": self.enabled,
        }


@dataclass
class PermissionCheckResult:
    """权限检查结果"""
    allowed: bool
    behavior: PermissionBehavior
    reason: str = ""
    rule: Optional[PermissionRule] = None
    requires_interaction: bool = False

    @classmethod
    def allow(cls, reason: str = "") -> "PermissionCheckResult":
        return cls(allowed=True, behavior=PermissionBehavior.ALLOW, reason=reason)

    @classmethod
    def deny(cls, reason: str = "", rule: Optional[PermissionRule] = None) -> "PermissionCheckResult":
        return cls(allowed=False, behavior=PermissionBehavior.DENY, reason=reason, rule=rule)

    @classmethod
    def ask(cls, reason: str = "") -> "PermissionCheckResult":
        return cls(allowed=False, behavior=PermissionBehavior.ASK, reason=reason, requires_interaction=True)


# ============================================================================
# BaseTool 抽象基类
# ============================================================================

class BaseTool(ABC):
    """
    工具基类。

    所有 OpenClaw 工具必须继承此类。
    参考 Claude Code 的 buildTool() 工厂函数设计。

    子类必须定义：
        name: str           - 工具唯一名称
        description: str    - 工具描述（AI 用于理解工具用途）

    可选覆盖：
        category: ToolCategory       - 工具分类
        tags: Set[str]               - 标签
        aliases: List[str]           - 别名
        is_enabled(): bool           - 是否启用
        validate_input(): ToolResult - 输入验证
        check_permissions(): PermissionCheckResult - 权限检查
        is_read_only(): bool         - 是否只读
        is_destructive(): bool        - 是否有破坏性
        get_activity_description(): str - 活动描述（用于显示）

    用法示例：
        class PortfolioTool(BaseTool):
            name = "portfolio"
            description = "获取账户和持仓信息"

            def is_read_only(self) -> bool:
                return True

            def validate_input(self, input_data: Dict) -> ToolResult | None:
                return None  # 无验证错误

            def call(self, ctx: ToolContext, input_data: Dict) -> ToolResult:
                portfolio = get_portfolio()
                return ToolResult.success_result(data=portfolio)
    """

    # 类属性（子类必须定义）
    name: str = ""
    description: str = ""

    # 可选类属性
    category: ToolCategory = ToolCategory.GENERAL
    tags: Set[str] = field(default_factory=set)
    aliases: List[str] = field(default_factory=list)
    version: str = "1.0.0"

    # Feature flag 名（如果工具依赖特性开关）
    feature_flag: Optional[str] = None

    # 上下文（实例化后由 ToolRegistry 注入）
    _registry: Optional["ToolRegistry"] = field(default=None, repr=False)

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description=self.description,
            category=self.category.value if isinstance(self.category, Enum) else self.category,
            tags=self.tags,
            version=self.version,
            aliases=self.aliases,
        )

    def is_enabled(self) -> bool:
        """工具是否启用（可被子类override）"""
        if self.feature_flag:
            from openclaw.feature_flags import is_feature_enabled
            return is_feature_enabled(self.feature_flag)
        return True

    def validate_input(self, input_data: Dict[str, Any]) -> Optional[ToolResult]:
        """
        验证输入参数。

        返回 None 表示验证通过。
        返回 ToolResult 表示验证失败。
        """
        return None

    def check_permissions(self, ctx: ToolContext, input_data: Dict[str, Any]) -> PermissionCheckResult:
        """
        权限检查。

        默认实现：使用 registry 的全局规则。
        子类可覆盖自定义权限逻辑。
        """
        if self._registry:
            return self._registry.check_tool_permissions(self.name, ctx, input_data)

        # 默认：使用上下文的权限模式
        if ctx.permission_mode == PermissionMode.ALLOW.value:
            return PermissionCheckResult.allow()
        elif ctx.permission_mode == PermissionMode.DENY.value:
            return PermissionCheckResult.deny("Permission mode is DENY")
        return PermissionCheckResult.allow()

    def is_read_only(self, input_data: Optional[Dict] = None) -> bool:
        """是否只读操作（默认 True，子类覆盖）"""
        return True

    def is_destructive(self, input_data: Optional[Dict] = None) -> bool:
        """是否有破坏性操作（默认 False）"""
        return False

    def requires_interaction(self) -> bool:
        """是否需要用户交互"""
        return False

    def get_activity_description(self, input_data: Optional[Dict]) -> Optional[str]:
        """返回活动描述，如 'Reading file foo.txt'"""
        return None

    def get_tool_use_summary(self, input_data: Optional[Dict]) -> Optional[str]:
        """返回简短摘要，用于紧凑显示"""
        return None

    @abstractmethod
    def call(self, ctx: ToolContext, input_data: Dict[str, Any]) -> ToolResult:
        """
        执行工具。

        必须由子类实现。

        Args:
            ctx: 工具执行上下文
            input_data: 经过验证的输入参数

        Returns:
            ToolResult: 执行结果
        """
        ...

    def execute(self, ctx: ToolContext, input_data: Dict[str, Any]) -> ToolResult:
        """
        工具执行的入口包装器。

        包含：输入验证 → 权限检查 → 执行 → 结果包装
        不要在子类中覆盖此方法；要覆盖 call()。
        """
        start_time = time.time()

        # 1. 权限模式检查（先于验证）
        permission = self.check_permissions(ctx, input_data)
        if not permission.allowed:
            return ToolResult.denied_result(
                reason=f"Permission denied: {permission.reason}"
            )

        # 2. 输入验证
        validation_error = self.validate_input(input_data)
        if validation_error:
            return validation_error

        # 3. 权限检查（精确）
        permission = self.check_permissions(ctx, input_data)
        if permission.requires_interaction:
            return ToolResult(
                success=False,
                error=f"Requires user interaction: {permission.reason}",
                status=ToolResultStatus.DENIED,
                requires_interaction=True,
            )

        # 4. 执行
        try:
            result = self.call(ctx, input_data)
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            return ToolResult.error_result(
                error=f"Tool execution failed: {str(e)}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"


# ============================================================================
# 工具注册表（增强版）
# ============================================================================

class ToolRegistry:
    """
    统一工具注册表。

    管理所有工具的注册、发现、权限、过滤。

    用法:
        registry = ToolRegistry()

        @registry.register
        class MyTool(BaseTool):
            name = "my_tool"
            ...

        tool = registry.get("my_tool")
        result = tool.execute(ctx, {"param": "value"})
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._rules: List[PermissionRule] = []
        self._lock = threading.RLock()
        self._permission_mode: PermissionMode = PermissionMode.DEFAULT
        self._initialized = False
        # 统计
        self._stats = {
            "total_calls": 0,
            "cache_hits": 0,
            "denials": 0,
        }

    def register(self, tool_cls: Optional[Type[BaseTool]] = None, *, name: Optional[str] = None) -> Type[BaseTool]:
        """
        装饰器用法：
            @registry.register
            class MyTool(BaseTool):
                name = "my_tool"
                ...

        直接调用用法：
            registry.register(MyTool)
        """
        def decorator(cls: Type[BaseTool]) -> Type[BaseTool]:
            instance = cls()
            tool_name = name or instance.name
            if not tool_name:
                raise ValueError(f"Tool class {cls.__name__} has no name")

            with self._lock:
                self._tools[tool_name] = instance
                instance._registry = self
                # 注册别名
                for alias in instance.aliases:
                    self._tools[alias] = instance

            return cls

        if tool_cls is None:
            return decorator
        else:
            return decorator(tool_cls)

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具实例（按名称或别名）"""
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> BaseTool:
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found")
        return tool

    def list_all(self) -> List[BaseTool]:
        """列出所有已注册的工具"""
        return list(self._tools.values())

    def list_enabled(self) -> List[BaseTool]:
        """列出所有已启用且 feature flag 开启的工具"""
        return [t for t in self._tools.values() if t.is_enabled()]

    def list_by_category(self, category: ToolCategory) -> List[BaseTool]:
        """按分类列出工具"""
        return [t for t in self._tools.values()
                if t.category == category and t.is_enabled()]

    def list_names(self, enabled_only: bool = False) -> List[str]:
        """列出所有工具名称"""
        seen = set()
        result = []
        for t in (self.list_enabled() if enabled_only else self.list_all()):
            if t.name not in seen:
                result.append(t.name)
                seen.add(t.name)
        return result

    def add_rule(self, rule: PermissionRule) -> None:
        """添加权限规则"""
        with self._lock:
            self._rules.append(rule)

    def set_permission_mode(self, mode: PermissionMode) -> None:
        """设置全局权限模式"""
        self._permission_mode = mode

    def check_tool_permissions(
        self, tool_name: str, ctx: ToolContext, input_data: Optional[Dict] = None
    ) -> PermissionCheckResult:
        """检查工具权限"""
        # 1. 全局权限模式优先
        if self._permission_mode == PermissionMode.ALLOW:
            return PermissionCheckResult.allow("Global mode ALLOW")
        if self._permission_mode == PermissionMode.DENY:
            return PermissionCheckResult.deny("Global mode DENY")

        # 2. 精确匹配规则
        with self._lock:
            for rule in reversed(self._rules):  # 后添加的优先
                if rule.tool_name == tool_name or rule.tool_name == "*":
                    if rule.rule_content is None:
                        # 通用规则
                        if rule.behavior == PermissionBehavior.DENY:
                            return PermissionCheckResult.deny(
                                reason=f"Blocked by rule: {rule.description}",
                                rule=rule,
                            )
                        elif rule.behavior == PermissionBehavior.ASK:
                            return PermissionCheckResult.ask(
                                reason=f"Requires confirmation: {rule.description}",
                            )
                    elif input_data and rule.matches(tool_name, input_data):
                        if rule.behavior == PermissionBehavior.DENY:
                            return PermissionCheckResult.deny(
                                reason=f"Blocked by rule: {rule.description}",
                                rule=rule,
                            )
                        elif rule.behavior == PermissionBehavior.ASK:
                            return PermissionCheckResult.ask(
                                reason=f"Requires confirmation: {rule.description}",
                            )

        return PermissionCheckResult.allow()

    def stats(self) -> Dict[str, Any]:
        """注册表统计"""
        all_tools = self.list_all()
        enabled = self.list_enabled()
        categories: Dict[str, int] = {}
        for t in all_tools:
            cat = t.category.value if isinstance(t.category, Enum) else t.category
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_registered": len(set(t.name for t in all_tools)),
            "total_enabled": len(set(t.name for t in enabled)),
            "categories": categories,
            "rules_count": len(self._rules),
            "permission_mode": self._permission_mode.value if isinstance(self._permission_mode, Enum) else self._permission_mode,
            "stats": self._stats,
        }


# ============================================================================
# 全局单例
# ============================================================================

tool_registry = ToolRegistry()


# ============================================================================
# 便捷装饰器
# ============================================================================

def register_tool(cls: Optional[Type[BaseTool]] = None, *, name: Optional[str] = None) -> Type[BaseTool]:
    """全局注册装饰器"""
    return tool_registry.register(cls, name=name)


# ============================================================================
# 危险命令模式库（参考 Claude Code 的 dangerousPatterns.ts）
# ============================================================================

DANGEROUS_PATTERNS: List[str] = [
    # 磁盘操作
    "rm -rf /",
    "rm -rf /*",
    "dd if=* of=/dev/*",
    "mkfs",
    "fdisk",
    # 网络操作
    "curl.*\|.*sh",
    "wget.*\|.*sh",
    "nc -e /bin/sh",
    "nc -e /bin/bash",
    "ncat.*-e",
    # 进程操作
    "kill -9 -1",
    "killall",
    # 系统修改
    "chmod 777 /etc/*",
    "chmod -R 777 /",
    "sudo rm -rf",
    # 密码/密钥
    "*password*",
    "*secret*",
    "*api_key*",
    # 交易相关危险操作
    "rm -rf data/*",
    "DROP TABLE",
    "DELETE FROM.*WHERE",
]


def is_dangerous_command(command: str) -> Tuple[bool, str]:
    """
    检查命令是否危险。

    Returns:
        (是否危险, 原因)
    """
    import re
    cmd_lower = command.lower()

    # 直接匹配危险模式
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            return True, f"危险命令模式: {pattern}"

    # rm -rf 双重确认
    if "rm -rf" in command and ("/" in command or "*" in command):
        return True, "rm -rf 包含路径或通配符"

    return False, ""
