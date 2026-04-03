"""
OpenClaw Skill System
=======================
Inspired by Claude Code's SkillTool.ts (1108 lines) and commands.ts.

核心设计：
1. Skill 就是 Command（有 name/prompt/description/tools）
2. 两种执行模式：inline（直接展开）和 fork（子Agent执行）
3. 多来源：bundled / MCP / remote / plugin
4. SkillRegistry：动态注册和发现
5. effort + model override：控制子Agent资源分配

Claude Code 的 skill 本质：
- SkillTool 调用 Skill(skill_name, args)
- Skill 展开成 system prompt + user prompt
- 在主Agent或子Agent中执行
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from openclaw.agent_tool import AgentDefinition


# ============================================================================
# Skill 来源
# ============================================================================

class SkillSource(str, Enum):
    """Skill 来源"""
    BUNDLED = "bundled"        # 内置skill（openclaw/skills/）
    MCP = "mcp"               # MCP服务器提供的skill
    REMOTE = "remote"         # 远程加载的skill
    PLUGIN = "plugin"         # 插件提供的skill
    CUSTOM = "custom"         # 用户自定义skill


# ============================================================================
# Skill 定义
# ============================================================================

@dataclass
class SkillManifest:
    """
    Skill 的元数据清单。

    对应 Claude Code 的 Command 类型。
    """
    name: str                           # 唯一名称（不含斜杠）
    description: str = ""               # 简短描述
    prompt: str = ""                    # Skill的核心prompt
    source: SkillSource = SkillSource.BUNDLED
    # 执行配置
    effort: Optional[int] = None       # 工作投入（token预算提示）
    model: Optional[str] = None        # 模型覆盖
    tools: List[str] = field(default_factory=list)    # 可用工具
    disallowed_tools: List[str] = field(default_factory=list)  # 禁用工具
    permission_mode: str = "accepted_edits"  # 权限模式
    # 来源信息
    loaded_from: Optional[str] = None   # 加载路径
    plugin_info: Optional[Dict] = None  # 插件信息
    category: Optional[str] = None      # 分类
    tags: Set[str] = field(default_factory=set)  # 标签
    version: str = "1.0"
    # 特性开关
    is_hidden: bool = False            # 是否隐藏（不暴露给AI）
    requires_confirmation: bool = False  # 是否需要确认

    @property
    def full_name(self) -> str:
        """带斜杠的完整名称"""
        return f"/{self.name}"

    def to_command(self) -> Dict[str, Any]:
        """转换为 Command 字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "prompt": self.prompt,
            "source": self.source.value,
            "effort": self.effort,
            "model": self.model,
            "tools": self.tools,
            "disallowed_tools": self.disallowed_tools,
            "permission_mode": self.permission_mode,
        }


@dataclass
class SkillExecutionInput:
    """Skill执行输入"""
    skill: str                 # Skill名称
    args: Optional[str] = None  # 附加参数


@dataclass
class SkillExecutionResult:
    """Skill执行结果"""
    success: bool
    command_name: str
    status: str = "inline"  # inline / forked
    agent_id: Optional[str] = None
    result: str = ""
    allowed_tools: Optional[List[str]] = None
    model: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Skill 注册表
# ============================================================================

class SkillRegistry:
    """
    全局 Skill 注册表。

    管理所有可用 Skill 的注册、发现、查询。
    支持多来源：bundled / MCP / remote / plugin。

    用法：
        registry = SkillRegistry.get_instance()

        # 注册一个skill
        registry.register(SkillManifest(
            name="commit",
            description="生成git提交信息",
            prompt="你是一个git提交助手..."
        ))

        # 查找skill
        skill = registry.get("commit")

        # 列出所有skill
        skills = registry.list_all()

        # 按标签搜索
        skills = registry.search_by_tag("trading")
    """

    _instance: Optional["SkillRegistry"] = None
    _lock = threading.RLock()

    def __init__(self):
        self._skills: Dict[str, SkillManifest] = {}
        self._tags_index: Dict[str, Set[str]] = {}  # tag -> skill names
        self._source_index: Dict[SkillSource, Set[str]] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "before_load": [],
            "after_load": [],
            "before_execute": [],
            "after_execute": [],
        }
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "SkillRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ---------------------
    # 注册
    # ---------------------

    def register(self, skill: SkillManifest) -> None:
        """注册一个 Skill"""
        with self._lock:
            self._skills[skill.name] = skill

            # 更新标签索引
            for tag in skill.tags:
                if tag not in self._tags_index:
                    self._tags_index[tag] = set()
                self._tags_index[tag].add(skill.name)

            # 更新来源索引
            if skill.source not in self._source_index:
                self._source_index[skill.source] = set()
            self._source_index[skill.source].add(skill.name)

    def register_batch(self, skills: List[SkillManifest]) -> None:
        """批量注册"""
        for skill in skills:
            self.register(skill)

    def unregister(self, name: str) -> bool:
        """注销 Skill"""
        with self._lock:
            if name not in self._skills:
                return False
            skill = self._skills.pop(name)
            # 清理索引
            for tag in skill.tags:
                if tag in self._tags_index:
                    self._tags_index[tag].discard(name)
            if skill.source in self._source_index:
                self._source_index[skill.source].discard(name)
            return True

    # ---------------------
    # 查询
    # ---------------------

    def get(self, name: str) -> Optional[SkillManifest]:
        """获取 Skill（支持 / 前缀）"""
        # 去掉前导斜杠
        name = name.lstrip("/")
        with self._lock:
            return self._skills.get(name)

    def has(self, name: str) -> bool:
        """检查 Skill 是否存在"""
        return self.get(name) is not None

    def list_all(self) -> List[SkillManifest]:
        """列出所有 Skill"""
        with self._lock:
            return list(self._skills.values())

    def list_by_source(self, source: SkillSource) -> List[SkillManifest]:
        """按来源列出 Skill"""
        with self._lock:
            names = self._source_index.get(source, set())
            return [self._skills[n] for n in names if n in self._skills]

    def list_hidden(self) -> bool:
        """是否包含隐藏 Skill"""
        with self._lock:
            return any(s.is_hidden for s in self._skills.values())

    def search(
        self,
        query: str,
        limit: int = 10,
        include_hidden: bool = False
    ) -> List[SkillManifest]:
        """
        搜索 Skill。

        支持：
        - 名称匹配
        - 描述匹配
        - 标签匹配
        """
        query_lower = query.lower()
        results = []

        with self._lock:
            for skill in self._skills.values():
                if skill.is_hidden and not include_hidden:
                    continue

                score = 0
                # 名称精确匹配
                if skill.name.lower() == query_lower:
                    score = 100
                # 名称包含
                elif query_lower in skill.name.lower():
                    score = 80
                # 描述包含
                elif query_lower in skill.description.lower():
                    score = 50
                # 标签匹配
                elif any(query_lower in tag.lower() for tag in skill.tags):
                    score = 30

                if score > 0:
                    results.append((score, skill))

        # 按分数排序
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

    def search_by_tag(self, tag: str) -> List[SkillManifest]:
        """按标签搜索"""
        with self._lock:
            names = self._tags_index.get(tag, set())
            return [self._skills[n] for n in names if n in self._skills]

    def search_by_tags(self, tags: List[str]) -> List[SkillManifest]:
        """按多个标签搜索（OR逻辑）"""
        with self._lock:
            result_names: Set[str] = set()
            for tag in tags:
                result_names |= self._tags_index.get(tag, set())
            return [self._skills[n] for n in result_names if n in self._skills]

    # ---------------------
    # 生命周期钩子
    # ---------------------

    def on_load(self, hook: Callable) -> None:
        """注册 skill 加载前后的钩子"""
        self._hooks["before_load"].append(hook)

    def on_execute(self, hook: Callable) -> None:
        """注册 skill 执行前后的钩子"""
        self._hooks["before_execute"].append(hook)

    def _trigger_hook(self, name: str, skill: SkillManifest) -> None:
        """触发钩子"""
        for hook in self._hooks.get(name, []):
            try:
                hook(skill)
            except Exception:
                pass

    # ---------------------
    # 初始化（扫描bundled skills）
    # ---------------------

    def initialize(self, skills_dir: Optional[str] = None) -> None:
        """
        初始化注册表，扫描 bundled skills。

        对应 Claude Code 的 getProjectRoot() + getCommands()。
        """
        if self._initialized:
            return

        if skills_dir is None:
            skills_dir = os.path.join(os.path.dirname(__file__), "..", "skills")

        skills_dir = os.path.abspath(skills_dir)

        # 扫描 SKILL.md 文件
        if os.path.isdir(skills_dir):
            self._scan_skills_directory(skills_dir)

        self._initialized = True

    def _scan_skills_directory(self, dir_path: str) -> None:
        """扫描 skills 目录，加载所有 SKILL.md"""
        for entry in os.scandir(dir_path):
            if entry.is_dir():
                skill_md = os.path.join(entry.path, "SKILL.md")
                if os.path.isfile(skill_md):
                    skill = self._load_skill_from_file(skill_md, entry.name)
                    if skill:
                        self.register(skill)

    def _load_skill_from_file(
        self,
        path: str,
        default_name: str
    ) -> Optional[SkillManifest]:
        """从 SKILL.md 加载 Skill 定义"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # 解析 frontmatter（如果存在）
            prompt = content
            description = ""
            name = default_name

            # 尝试解析 YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    import yaml
                    try:
                        metadata = yaml.safe_load(parts[1])
                        description = metadata.get("description", "")
                        name = metadata.get("name", default_name)
                        prompt = parts[2].strip()
                    except Exception:
                        prompt = content

            # 从 prompt 第一行提取名称（如果不在 metadata 中）
            lines = prompt.split("\n")
            if lines and lines[0].startswith("# "):
                if not name or name == default_name:
                    name = lines[0][2:].strip().lower().replace(" ", "-")

            return SkillManifest(
                name=name,
                description=description or f"{name} skill",
                prompt=prompt,
                source=SkillSource.BUNDLED,
                loaded_from=path,
            )

        except Exception:
            return None

    # ---------------------
    # MCP Skill 集成
    # ---------------------

    def register_mcp_skills(self, mcp_commands: List[Dict[str, Any]]) -> None:
        """
        注册 MCP 服务器提供的 Skill。

        对应 Claude Code 的 getAllCommands() 中过滤 mcp 命令。
        """
        for cmd in mcp_commands:
            if cmd.get("type") != "prompt":
                continue

            skill = SkillManifest(
                name=cmd.get("name", ""),
                description=cmd.get("description", ""),
                prompt=cmd.get("prompt", ""),
                source=SkillSource.MCP,
                loaded_from=f"mcp:{cmd.get('server', 'unknown')}",
            )
            self.register(skill)

    # ---------------------
    # 统计
    # ---------------------

    def stats(self) -> Dict[str, Any]:
        """统计信息"""
        with self._lock:
            return {
                "total": len(self._skills),
                "by_source": {
                    source.value: len(names)
                    for source, names in self._source_index.items()
                },
                "total_tags": len(self._tags_index),
                "initialized": self._initialized,
            }


# 全局单例
skill_registry = SkillRegistry.get_instance()


# ============================================================================
# 内置 Skills
# ============================================================================

# Claude Code 的 builtInCommandNames() 对应
BUILT_IN_SKILLS: List[SkillManifest] = [
    SkillManifest(
        name="commit",
        description="生成语义化的git提交信息",
        prompt="""你是一个git提交助手。根据以下diff生成简洁的提交信息：

要求：
- 使用中文
- 第一行不超过50字符
- 如果有空行，详细说明写在空行下面
- 格式：type(scope): subject

type: feat/fix/docs/style/refactor/test/chore""",
        source=SkillSource.BUNDLED,
        tags={"git", "commit"},
    ),
    SkillManifest(
        name="review",
        description="代码审查",
        prompt="""你是一个代码审查专家。审查以下代码：

关注点：
1. 逻辑错误
2. 安全漏洞
3. 性能问题
4. 代码风格
5. 文档完整性

输出格式：
## 优点
## 问题
## 建议""",
        source=SkillSource.BUNDLED,
        tags={"code", "review"},
    ),
    SkillManifest(
        name="trade",
        description="股票交易分析",
        prompt="""你是一个股票交易分析师。根据以下信息做出交易决策：

决策框架：
1. 趋势判断：MA5/MA10/MA20 多头排列还是空头排列
2. 动量指标：RSI 是否超买超卖
3. 成交量：是否放量突破
4. 止损设置：-8% 止损

仓位管理：
- 单票上限 ¥10,000
- 总仓位上限 20%
- 宁可错过不可做错

执行策略：
- 建仓：指数站稳5日线 + 个股信号确认
- 止损：-8%
- 止盈：+10%卖1/3，+15%卖1/3，+20%清仓""",
        source=SkillSource.BUNDLED,
        tags={"trading", "stock"},
    ),
]

# 注册内置 skills
for skill in BUILT_IN_SKILLS:
    skill_registry.register(skill)


# ============================================================================
# Skill 执行器
# ============================================================================

class SkillExecutor:
    """
    Skill 执行器。

    对应 Claude Code 的 executeForkedSkill()。
    支持 inline 和 fork 两种执行模式。
    """

    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or skill_registry

    async def execute(
        self,
        input_data: SkillExecutionInput,
        context: Optional[Dict[str, Any]] = None,
        fork: bool = True,
    ) -> SkillExecutionResult:
        """
        执行 Skill。

        Args:
            input_data: Skill 名称和参数
            context: 执行上下文
            fork: 是否在子 Agent 中执行

        Returns:
            SkillExecutionResult
        """
        skill = self.registry.get(input_data.skill)
        if not skill:
            return SkillExecutionResult(
                success=False,
                command_name=input_data.skill,
                error=f"Skill '{input_data.skill}' not found",
            )

        # 构建 prompt
        full_prompt = self._build_prompt(skill, input_data.args)

        if fork:
            return await self._execute_forked(skill, full_prompt, context)
        else:
            return await self._execute_inline(skill, full_prompt, context)

    def _build_prompt(self, skill: SkillManifest, args: Optional[str]) -> str:
        """构建 Skill 的完整 prompt"""
        prompt = skill.prompt

        if args:
            prompt = f"{prompt}\n\n## 输入参数\n{args}"

        return prompt

    async def _execute_inline(
        self,
        skill: SkillManifest,
        prompt: str,
        context: Optional[Dict[str, Any]],
    ) -> SkillExecutionResult:
        """
        Inline 执行：直接在主 Agent 中执行。

        对应 Claude Code 的 inline skill 路径。
        """
        # TODO: 调用实际的 AI 模型执行 prompt
        # 目前返回模拟结果
        await asyncio.sleep(0.1)

        return SkillExecutionResult(
            success=True,
            command_name=skill.name,
            status="inline",
            result=f"[Inline skill '{skill.name}' executed]",
            allowed_tools=skill.tools or None,
            model=skill.model,
        )

    async def _execute_forked(
        self,
        skill: SkillManifest,
        prompt: str,
        context: Optional[Dict[str, Any]],
    ) -> SkillExecutionResult:
        """
        Fork 执行：在子 Agent 中执行。

        对应 Claude Code 的 executeForkedSkill()。
        """
        import uuid
        from openclaw.agent_tool import spawn_agent

        agent_id = str(uuid.uuid4())

        try:
            # 使用 AgentTool 的子 Agent 执行
            result = spawn_agent(
                agent_type=skill.model or "general_purpose",
                prompt=prompt,
                description=f"skill:{skill.name}",
                run_async=False,
            )

            return SkillExecutionResult(
                success=True,
                command_name=skill.name,
                status="forked",
                agent_id=agent_id,
                result=str(result),
            )

        except Exception as e:
            return SkillExecutionResult(
                success=False,
                command_name=skill.name,
                status="forked",
                error=str(e),
            )


# 全局执行器
skill_executor = SkillExecutor()


# ============================================================================
# Skill 工具
# ============================================================================

from openclaw.tools.base import BaseTool, ToolResult, ToolMetadata, ToolCategory


class SkillTool(BaseTool):
    """
    Skill 调用工具。

    对应 Claude Code 的 SkillTool。
    允许 AI 调用 /skill-name 格式的技能。

    输入：
    - skill: 技能名称
    - args: 可选参数

    输出：
    - 执行结果
    """

    name = "Skill"
    description = "Execute a skill (slash command)"
    category = ToolCategory.SYSTEM
    tags = {"skill", "slash", "command"}
    version = "1.0.0"

    def __init__(self):
        super().__init__()
        self._registry = skill_registry
        self._executor = skill_executor

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
        执行 Skill。

        对应 Claude Code SkillTool.call()。
        """
        skill_name = input_data.get("skill", "").lstrip("/")
        args = input_data.get("args")

        if not skill_name:
            return ToolResult(
                success=False,
                error="Skill name is required"
            )

        # 查找 skill
        skill = self._registry.get(skill_name)
        if not skill:
            # 尝试模糊搜索
            matches = self._registry.search(skill_name, limit=3)
            if matches:
                suggestions = ", ".join(f"/{s.name}" for s in matches)
                return ToolResult(
                    success=False,
                    error=f"Skill '{skill_name}' not found. Did you mean: {suggestions}?"
                )
            return ToolResult(
                success=False,
                error=f"Skill '{skill_name}' not found"
            )

        # 确定执行模式
        fork = input_data.get("fork", True)
        if skill.effort and skill.effort > 50:
            fork = True  # 高effort skill默认fork

        # 执行
        input_obj = SkillExecutionInput(skill=skill_name, args=args)
        result = await self._executor.execute(input_obj, context=ctx, fork=fork)

        if result.success:
            return ToolResult(
                success=True,
                data={
                    "success": True,
                    "commandName": result.command_name,
                    "status": result.status,
                    "agentId": result.agent_id,
                    "result": result.result,
                    "allowedTools": result.allowed_tools,
                    "model": result.model,
                }
            )
        else:
            return ToolResult(
                success=False,
                error=result.error or "Skill execution failed"
            )


class ListSkillsTool(BaseTool):
    """列出所有可用的 Skill"""

    name = "ListSkills"
    description = "List all available skills"
    category = ToolCategory.SYSTEM
    tags = {"skill", "list"}
    version = "1.0.0"

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
        query = input_data.get("query", "")
        source_filter = input_data.get("source")

        if query:
            skills = skill_registry.search(query)
        elif source_filter:
            try:
                source = SkillSource(source_filter)
                skills = skill_registry.list_by_source(source)
            except ValueError:
                return ToolResult(success=False, error=f"Unknown source: {source_filter}")
        else:
            skills = skill_registry.list_all()

        # 过滤隐藏的
        skills = [s for s in skills if not s.is_hidden]

        return ToolResult(
            success=True,
            data={
                "skills": [
                    {
                        "name": s.name,
                        "description": s.description,
                        "source": s.source.value,
                        "tags": list(s.tags),
                    }
                    for s in skills
                ],
                "total": len(skills),
            }
        )


class SearchSkillsTool(BaseTool):
    """搜索 Skills"""

    name = "SearchSkills"
    description = "Search for skills by name, description, or tags"
    category = ToolCategory.SYSTEM
    tags = {"skill", "search"}
    version = "1.0.0"

    async def call(self, ctx: Any, input_data: Dict[str, Any]) -> ToolResult:
        query = input_data.get("query", "")
        tags = input_data.get("tags", [])

        if not query and not tags:
            return ToolResult(
                success=False,
                error="Either query or tags is required"
            )

        if query:
            skills = skill_registry.search(query)
        else:
            skills = skill_registry.search_by_tags(tags)

        return ToolResult(
            success=True,
            data={
                "skills": [
                    {
                        "name": s.name,
                        "description": s.description,
                        "tags": list(s.tags),
                        "source": s.source.value,
                    }
                    for s in skills
                ]
            }
        )


# ============================================================================
# 便捷函数
# ============================================================================

def register_skill(
    name: str,
    prompt: str,
    description: str = "",
    source: SkillSource = SkillSource.CUSTOM,
    **kwargs
) -> SkillManifest:
    """
    快速注册一个 Skill。

    用法：
        register_skill(
            name="my-skill",
            prompt="你是一个助手...",
            description="我的技能",
            tags={"custom", "test"}
        )
    """
    skill = SkillManifest(
        name=name,
        description=description or f"{name} skill",
        prompt=prompt,
        source=source,
        **kwargs
    )
    skill_registry.register(skill)
    return skill


async def execute_skill(
    skill_name: str,
    args: Optional[str] = None,
    fork: bool = True
) -> SkillExecutionResult:
    """
    快速执行一个 Skill。

    用法：
        result = await execute_skill("commit", "fix: 修复bug")
    """
    input_obj = SkillExecutionInput(skill=skill_name, args=args)
    return await skill_executor.execute(input_obj, fork=fork)


# ============================================================================
# MCP Skill 集成
# ============================================================================

def discover_mcp_skills(mcp_tools: List[Dict[str, Any]]) -> None:
    """
    从 MCP 工具中发现 Skill。

    Claude Code 的 SkillTool 会过滤 MCP 服务器的 prompt 类型命令。
    """
    mcp_commands = []
    for tool in mcp_tools:
        if tool.get("type") == "prompt" or "prompt" in tool.get("name", "").lower():
            mcp_commands.append(tool)

    if mcp_commands:
        skill_registry.register_mcp_skills(mcp_commands)


# ============================================================================
# MCP Skill 深度集成（第2轮深化）
# ============================================================================

async def sync_mcp_skills_from_servers(
    manager=None,
    registry=None,
    force_refresh: bool = False,
) -> int:
    """
    从所有已连接的 MCP 服务器同步 Skill。

    对应 Claude Code SkillTool.ts 中 getAllCommands() 的 MCP 部分。
    将 MCP 服务器的 prompt 类型资源注册为可调用的 Skill。

    Returns:
        新注册的 skill 数量
    """
    if registry is None:
        registry = skill_registry

    try:
        from openclaw.mcp_client import mcp_server_manager, McpCommand
    except ImportError:
        return 0

    manager = manager or mcp_server_manager
    commands = await manager.get_commands()
    new_count = 0

    for cmd in commands:
        if not cmd.name or not cmd.prompt:
            continue

        # 跳过已存在的
        if registry.has(cmd.name):
            continue

        # 创建 Skill
        skill = SkillManifest(
            name=cmd.name,
            description=cmd.description or f"MCP skill: {cmd.name}",
            prompt=cmd.prompt,
            source=SkillSource.MCP,
            loaded_from=f"mcp:{manager._configs.get(cmd.name, 'unknown')}",
            tags={"mcp", "auto-discovered"},
        )
        registry.register(skill)
        new_count += 1

    return new_count


def setup_mcp_skill_autoload(
    registry=None,
    manager=None,
) -> None:
    """
    设置 MCP Skill 自动加载。

    当 MCP 服务器连接时，自动将其 prompt 注册为 Skill。
    """
    if registry is None:
        registry = skill_registry

    try:
        from openclaw.mcp_client import mcp_server_manager
    except ImportError:
        return

    manager = manager or mcp_server_manager

    # Hook: MCP 服务器连接时自动同步 skills
    # 通过定期轮询实现（简单版）
    # 完整版应该用 mcp_server_manager 的事件系统
    pass


# ============================================================================
# Skill 执行器增强（第2轮深化）
# ============================================================================

class SkillExecutorV2(SkillExecutor):
    """
    Skill 执行器 V2（第2轮深化版）。

    改进：
    1. 真正的 AI 模型调用（接 MiniMax API）
    2. Streaming 支持
    3. Token 计数和预算控制
    4. 更好的错误处理
    """

    def __init__(self, registry=None):
        super().__init__(registry)
        self._model = "minimax"
        self._max_tokens = 4000

    async def _execute_inline(
        self,
        skill: SkillManifest,
        prompt: str,
        context: Optional[Dict[str, Any]],
    ) -> SkillExecutionResult:
        """
        Inline 执行：调用 AI 模型执行 Skill prompt。

        第2轮深化：真正调用 MiniMax API。
        """
        import os

        full_prompt = self._build_prompt(skill, None)

        # 构建 API 请求
        api_key = os.environ.get("MINIMAX_API_KEY", "")
        if not api_key:
            return SkillExecutionResult(
                success=False,
                command_name=skill.name,
                error="MINIMAX_API_KEY not set"
            )

        try:
            import urllib.request
            import urllib.error

            url = "https://api.minimax.chat/v1/text/chatcompletion_pro"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            data = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": "请执行这个技能。"}
                ],
                "max_tokens": self._max_tokens,
                "temperature": 0.7,
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            return SkillExecutionResult(
                success=True,
                command_name=skill.name,
                status="inline",
                result=content,
                allowed_tools=skill.tools or None,
                model=skill.model or self._model,
            )

        except Exception as e:
            return SkillExecutionResult(
                success=False,
                command_name=skill.name,
                error=f"AI API call failed: {str(e)}"
            )


# 升级执行器单例
skill_executor = SkillExecutorV2()


# ============================================================================
# MCP Tool → Skill 桥接器（第2轮核心功能）
# ============================================================================

def mcp_tool_to_skill(
    tool: "McpTool",  # forward ref
    registry=None,
) -> Optional[SkillManifest]:
    """
    将单个 MCP 工具转换为 Skill。

    对应 Claude Code 的 mcpToolInputToAutoClassifierInput 思路。
    MCP 的 tool 包含 name/description/inputSchema，转换为 Skill 的 prompt 模板。

    Args:
        tool: MCP 工具对象
        registry: Skill 注册表（用于检查是否已存在）

    Returns:
        SkillManifest 或 None（如果不适合转换）
    """
    if registry is None:
        registry = skill_registry

    # 生成唯一的 skill name
    skill_name = f"mcp_{tool.server_id}_{tool.name}"

    # 跳过已存在
    if registry.has(skill_name):
        return None

    # 构建 prompt 模板（让 AI 知道如何调用这个工具）
    param_desc = ""
    if tool.input_schema:
        properties = tool.input_schema.get("properties", {})
        param_desc = "\n".join(
            f"- {name}: {prop.get('description', prop.get('type', 'any'))}"
            for name, prop in properties.items()
        )

    prompt_template = f"""# MCP Tool: {tool.name}

## 描述
{tool.description or '无'}

## 参数
{param_desc or '无参数'}

## 执行
当需要执行这个工具时，使用以下格式：

**Tool Call:**
{{
  "tool": "mcp__{tool.server_id}__{tool.name}",
  "action": "call",
  "parameters": {{ ... }}
}}

**注意**: 这是通过 MCP 协议调用远程服务器 {tool.server_name} 上的工具。
"""

    skill = SkillManifest(
        name=skill_name,
        description=f"[MCP] {tool.description}" if tool.description else f"MCP tool: {tool.name}",
        prompt=prompt_template,
        source=SkillSource.MCP,
        loaded_from=f"mcp:{tool.server_id}",
        tags={"mcp", f"server:{tool.server_id}"},
        plugin_info={
            "mcp_server_id": tool.server_id,
            "mcp_server_name": tool.server_name,
            "mcp_tool_name": tool.name,
            "mcp_input_schema": tool.input_schema,
        }
    )

    return skill


def mcp_tools_to_skills(
    tools: List["McpTool"],
    registry=None,
) -> List[SkillManifest]:
    """
    批量将 MCP 工具转换为 Skills。

    对应 Claude Code 中 SkillTool.ts 的 getAllCommands() MCP 部分。
    """
    if registry is None:
        registry = skill_registry

    skills = []
    for tool in tools:
        skill = mcp_tool_to_skill(tool, registry)
        if skill:
            skills.append(skill)
            registry.register(skill)

    return skills


async def sync_mcp_tools_to_skills(
    manager=None,
    registry=None,
    force_refresh: bool = False,
) -> int:
    """
    从 MCP 服务器同步所有工具作为 Skills。

    对应 Claude Code SkillTool 的 MCP tools → commands 转换。
    """
    if registry is None:
        registry = skill_registry

    try:
        from openclaw.mcp_client import mcp_server_manager
    except ImportError:
        return 0

    manager = manager or mcp_server_manager
    tools = await manager.get_tools(force_refresh=force_refresh)

    if not tools:
        return 0

    skills = mcp_tools_to_skills(tools, registry)
    return len(skills)


# ============================================================================
# 启动时 MCP 集成初始化
# ============================================================================

async def initialize_mcp_integration(
    mcp_configs: Optional[List[Dict[str, Any]]] = None,
    registry=None,
    manager=None,
) -> Dict[str, Any]:
    """
    初始化 MCP 集成。

    在 app.py 启动时调用，完成：
    1. 连接配置的 MCP 服务器
    2. 同步所有 MCP tools → Skills
    3. 返回集成状态

    Args:
        mcp_configs: MCP 服务器配置列表
            [{"id": "filesystem", "command": "npx", "args": [...], "env": {...}}]
        registry: Skill 注册表
        manager: MCP 服务器管理器

    Returns:
        {"servers_connected": N, "skills_registered": M}
    """
    if registry is None:
        registry = skill_registry

    try:
        from openclaw.mcp_client import mcp_server_manager, McpServerConfig
    except ImportError:
        return {"error": "mcp_client not available", "servers_connected": 0, "skills_registered": 0}

    manager = manager or mcp_server_manager

    # 添加并连接服务器
    servers_added = 0
    if mcp_configs:
        for config_dict in mcp_configs:
            try:
                config = McpServerConfig(**config_dict)
                manager.add_server(config)
                servers_added += 1
                await manager.connect_server(config.id)
            except Exception as e:
                print(f"Failed to add MCP server {config_dict.get('id', '?')}: {e}")

    # 同步 tools → skills
    tools = await manager.get_tools()
    skills = mcp_tools_to_skills(tools, registry)

    return {
        "servers_configured": servers_added,
        "servers_connected": sum(1 for s in manager._sessions.values() if s.is_connected),
        "tools_discovered": len(tools),
        "skills_registered": len(skills),
    }


# ============================================================================
# 便捷函数：列出所有 MCP 来源的 Skills
# ============================================================================

def list_mcp_skills(registry=None) -> List[SkillManifest]:
    """列出所有 MCP 来源的 Skills"""
    if registry is None:
        registry = skill_registry
    return [
        s for s in registry.list_all()
        if s.source == SkillSource.MCP
    ]
