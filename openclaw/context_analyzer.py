"""
Context Analyzer - 上下文分析器
基于 Claude Code analyzeContext.ts 设计

分析AI对话的上下文窗口使用情况，包括：
- 系统提示词Token计数
- 工具定义Token计数
- 消息历史Token计数
- 记忆文件Token计数
- 技能Token计数
- 上下文可视化（网格）
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .errors import error_message, log_error


# Token计数开销（API在工具存在时添加约500 token）
TOOL_TOKEN_COUNT_OVERHEAD = 500

# 上下文窗口大小配置
CONTEXT_WINDOW_200K = 200000
CONTEXT_WINDOW_1M = 1000000


class ThemeColor(Enum):
    """主题颜色"""
    PROMPT_BORDER = "promptBorder"
    INACTIVE = "inactive"
    CYAN_FOR_SUBAGENTS_ONLY = "cyan_FOR_SUBAGENTS_ONLY"
    PERMISSION = "permission"
    CLAUDE = "claude"
    WARNING = "warning"
    PURPLE_FOR_SUBAGENTS_ONLY = "purple_FOR_SUBAGENTS_ONLY"


@dataclass
class ContextCategory:
    """上下文类别"""
    name: str
    tokens: int
    color: str
    is_deferred: bool = False


@dataclass
class GridSquare:
    """网格方块"""
    color: str
    is_filled: bool
    category_name: str
    tokens: int
    percentage: int
    square_fullness: float  # 0-1，部分填充的方块


@dataclass
class MemoryFile:
    """记忆文件"""
    path: str
    type: str
    tokens: int


@dataclass
class McpTool:
    """MCP工具"""
    name: str
    server_name: str
    tokens: int
    is_loaded: bool = True


@dataclass
class SkillInfo:
    """技能信息"""
    total_skills: int
    included_skills: int
    tokens: int
    skill_frontmatter: list[dict] = field(default_factory=list)


@dataclass
class MessageBreakdown:
    """消息分解"""
    tool_call_tokens: int = 0
    tool_result_tokens: int = 0
    attachment_tokens: int = 0
    assistant_message_tokens: int = 0
    user_message_tokens: int = 0
    tool_calls_by_type: list[dict] = field(default_factory=list)
    attachments_by_type: list[dict] = field(default_factory=list)


@dataclass
class ApiUsage:
    """API实际用量"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class ContextData:
    """
    上下文分析数据
    
    包含完整的上下文窗口使用情况分析结果。
    """
    categories: list[ContextCategory]
    total_tokens: int
    max_tokens: int
    raw_max_tokens: int
    percentage: int
    grid_rows: list[list[GridSquare]]
    model: str
    memory_files: list[MemoryFile] = field(default_factory=list)
    mcp_tools: list[McpTool] = field(default_factory=list)
    deferred_builtin_tools: list[dict] = field(default_factory=list)
    system_tools: list[dict] = field(default_factory=list)
    system_prompt_sections: list[dict] = field(default_factory=list)
    agents: list[dict] = field(default_factory=list)
    slash_commands: Optional[dict] = None
    skills: Optional[SkillInfo] = None
    auto_compact_threshold: Optional[int] = None
    is_auto_compact_enabled: bool = False
    message_breakdown: Optional[MessageBreakdown] = None
    api_usage: Optional[ApiUsage] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "categories": [
                {
                    "name": c.name,
                    "tokens": c.tokens,
                    "color": c.color,
                    "isDeferred": c.is_deferred,
                }
                for c in self.categories
            ],
            "totalTokens": self.total_tokens,
            "maxTokens": self.max_tokens,
            "rawMaxTokens": self.raw_max_tokens,
            "percentage": self.percentage,
            "gridRows": [
                [
                    {
                        "color": g.color,
                        "isFilled": g.is_filled,
                        "categoryName": g.category_name,
                        "tokens": g.tokens,
                        "percentage": g.percentage,
                        "squareFullness": g.square_fullness,
                    }
                    for g in row
                ]
                for row in self.grid_rows
            ],
            "model": self.model,
            "memoryFiles": [
                {"path": m.path, "type": m.type, "tokens": m.tokens}
                for m in self.memory_files
            ],
            "mcpTools": [
                {
                    "name": t.name,
                    "serverName": t.server_name,
                    "tokens": t.tokens,
                    "isLoaded": t.is_loaded,
                }
                for t in self.mcp_tools
            ],
            "messageBreakdown": self.message_breakdown.to_dict() if self.message_breakdown else None,
            "apiUsage": self.api_usage.to_dict() if self.api_usage else None,
        }


class ContextAnalyzer:
    """
    上下文分析器
    
    分析上下文窗口的使用情况，提供详细的Token计数和可视化。
    """
    
    def __init__(
        self,
        model: str = "claude-opus-4-5-20251120",
        context_window: int = CONTEXT_WINDOW_200K,
    ):
        self.model = model
        self.context_window = context_window
    
    def estimate_tokens(self, text: str) -> int:
        """简单Token估算（中文约2字符=1 token，英文约4字符=1 token）"""
        if not text:
            return 0
        
        # 简化的估算方法
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        # 中文约1.5字符/token，英文约4字符/token
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    async def count_system_tokens(self, system_prompt: str) -> tuple[int, list[dict]]:
        """
        计数系统提示词Token
        
        Returns:
            (tokens, sections)
        """
        if not system_prompt:
            return 0, []
        
        tokens = self.estimate_tokens(system_prompt)
        
        # 提取section名称
        sections = []
        for line in system_prompt.split("\n"):
            if line.startswith("#"):
                sections.append({
                    "name": line.lstrip("#").strip(),
                    "tokens": self.estimate_tokens(line),
                })
        
        return tokens, sections if sections else [{"name": "System prompt", "tokens": tokens}]
    
    async def count_memory_file_tokens(
        self,
        memory_files: list[dict],
    ) -> tuple[list[MemoryFile], int]:
        """
        计数记忆文件Token
        
        Args:
            memory_files: 记忆文件列表 [{"path": ..., "content": ..., "type": ...}]
            
        Returns:
            (file_details, total_tokens)
        """
        total = 0
        details = []
        
        for f in memory_files:
            content = f.get("content", "")
            tokens = self.estimate_tokens(content)
            total += tokens
            details.append(MemoryFile(
                path=f.get("path", ""),
                type=f.get("type", ""),
                tokens=tokens,
            ))
        
        return details, total
    
    async def count_tool_tokens(
        self,
        tools: list[dict],
    ) -> int:
        """
        计数工具定义Token
        
        Args:
            tools: 工具定义列表
            
        Returns:
            总Token数
        """
        if not tools:
            return 0
        
        total = 0
        for tool in tools:
            # 工具定义包括名称、描述、参数schema
            tool_str = json.dumps(tool, ensure_ascii=False)
            total += self.estimate_tokens(tool_str)
        
        # 减去开销（只计算一次）
        overhead = max(0, TOOL_TOKEN_COUNT_OVERHEAD)
        return max(0, total - overhead)
    
    async def count_message_tokens(
        self,
        messages: list[dict],
    ) -> MessageBreakdown:
        """
        计数消息Token
        
        Args:
            messages: 消息列表
            
        Returns:
            消息分解统计
        """
        breakdown = MessageBreakdown()
        
        for msg in messages:
            msg_type = msg.get("type", "")
            content = msg.get("message", {}).get("content", "")
            
            if isinstance(content, str):
                tokens = self.estimate_tokens(content)
                if msg_type == "user":
                    breakdown.user_message_tokens += tokens
                elif msg_type == "assistant":
                    breakdown.assistant_message_tokens += tokens
            elif isinstance(content, list):
                for block in content:
                    block_str = json.dumps(block, ensure_ascii=False)
                    tokens = self.estimate_tokens(block_str)
                    
                    if isinstance(block, dict):
                        if block.get("type") == "tool_use":
                            breakdown.tool_call_tokens += tokens
                            name = block.get("name", "unknown")
                            # 更新按类型统计
                            found = False
                            for t in breakdown.tool_calls_by_type:
                                if t["name"] == name:
                                    t["callTokens"] += tokens
                                    found = True
                                    break
                            if not found:
                                breakdown.tool_calls_by_type.append({
                                    "name": name,
                                    "callTokens": tokens,
                                    "resultTokens": 0,
                                })
                        elif block.get("type") == "tool_result":
                            breakdown.tool_result_tokens += tokens
                        else:
                            breakdown.assistant_message_tokens += tokens
                    else:
                        breakdown.assistant_message_tokens += tokens
        
        breakdown.tool_calls_by_type.sort(
            key=lambda x: x["callTokens"] + x["resultTokens"],
            reverse=True,
        )
        
        return breakdown
    
    def build_grid(
        self,
        categories: list[ContextCategory],
        terminal_width: Optional[int] = None,
    ) -> list[list[GridSquare]]:
        """
        构建上下文可视化网格
        
        Args:
            categories: 上下文类别
            terminal_width: 终端宽度
            
        Returns:
            网格行列表
        """
        # 确定网格尺寸
        is_narrow = terminal_width and terminal_width < 80
        if self.context_window >= CONTEXT_WINDOW_1M:
            grid_width = 5 if is_narrow else 20
            grid_height = 10
        else:
            grid_width = 5 if is_narrow else 10
            grid_height = 10
        
        total_squares = grid_width * grid_height
        
        # 计算每个类别占用的方块数
        category_squares = []
        for cat in categories:
            if cat.name == "Free space":
                squares = round((cat.tokens / self.context_window) * total_squares)
            else:
                squares = max(1, round((cat.tokens / self.context_window) * total_squares))
            
            percentage = round((cat.tokens / self.context_window) * 100)
            
            category_squares.append({
                **cat,
                "squares": squares,
                "percentage_of_total": percentage,
            })
        
        # 构建网格
        grid_squares: list[GridSquare] = []
        
        # 非reserved和非free-space的类别
        non_special = [
            c for c in category_squares
            if c.name not in ("Reserved buffer", "Compact buffer", "Free space")
        ]
        
        for cat in non_special:
            exact = (cat.tokens / self.context_window) * total_squares
            whole = int(exact)
            fractional = exact - whole
            
            for i in range(cat["squares"]):
                fullness = 1.0
                if i == whole and fractional > 0:
                    fullness = fractional
                
                grid_squares.append(GridSquare(
                    color=cat.color,
                    is_filled=True,
                    category_name=cat.name,
                    tokens=cat.tokens,
                    percentage=cat["percentage_of_total"],
                    square_fullness=fullness,
                ))
        
        # 计算reserved方块数
        reserved_cat = next(
            (c for c in category_squares if c.name in ("Reserved buffer", "Compact buffer")),
            None,
        )
        reserved_count = reserved_cat["squares"] if reserved_cat else 0
        
        # 填充free space
        free_space_cat = next(
            (c for c in categories if c.name == "Free space"),
            None,
        )
        free_space_target = total_squares - reserved_count
        
        while len(grid_squares) < free_space_target:
            grid_squares.append(GridSquare(
                color="promptBorder",
                is_filled=True,
                category_name="Free space",
                tokens=free_space_cat.tokens if free_space_cat else 0,
                percentage=free_space_cat.percentage if free_space_cat else 0,
                square_fullness=1.0,
            ))
        
        # 添加reserved方块
        if reserved_cat:
            exact = (reserved_cat.tokens / self.context_window) * total_squares
            whole = int(exact)
            fractional = exact - whole
            
            for i in range(reserved_count):
                fullness = 1.0
                if i == whole and fractional > 0:
                    fullness = fractional
                
                grid_squares.append(GridSquare(
                    color=reserved_cat.color,
                    is_filled=True,
                    category_name=reserved_cat.name,
                    tokens=reserved_cat.tokens,
                    percentage=reserved_cat["percentage_of_total"],
                    square_fullness=fullness,
                ))
        
        # 转换为行
        rows: list[list[GridSquare]] = []
        for i in range(grid_height):
            start = i * grid_width
            end = start + grid_width
            rows.append(grid_squares[start:end])
        
        return rows
    
    async def analyze(
        self,
        system_prompt: str,
        messages: list[dict],
        tools: list[dict],
        memory_files: list[dict],
        mcp_tools: list[dict],
        agents: list[dict],
        skills: list[dict],
        api_usage: Optional[dict] = None,
        terminal_width: Optional[int] = None,
    ) -> ContextData:
        """
        分析上下文使用情况
        
        Args:
            system_prompt: 系统提示词
            messages: 消息历史
            tools: 工具定义列表
            memory_files: 记忆文件列表
            mcp_tools: MCP工具列表
            agents: Agent定义列表
            skills: 技能列表
            api_usage: API实际用量
            terminal_width: 终端宽度
            
        Returns:
            上下文分析数据
        """
        categories: list[ContextCategory] = []
        
        # 1. 系统提示词
        system_tokens, system_sections = await self.count_system_tokens(system_prompt)
        if system_tokens > 0:
            categories.append(ContextCategory(
                name="System prompt",
                tokens=system_tokens,
                color="promptBorder",
            ))
        
        # 2. 内置工具
        tool_tokens = await self.count_tool_tokens(tools)
        if tool_tokens > 0:
            categories.append(ContextCategory(
                name="System tools",
                tokens=tool_tokens,
                color="inactive",
            ))
        
        # 3. MCP工具
        mcp_tool_tokens = await self.count_tool_tokens(mcp_tools)
        if mcp_tool_tokens > 0:
            categories.append(ContextCategory(
                name="MCP tools",
                tokens=mcp_tool_tokens,
                color="cyan_FOR_SUBAGENTS_ONLY",
            ))
        
        # 4. 自定义Agent
        agent_tokens = sum(self.estimate_tokens(json.dumps(a)) for a in agents)
        if agent_tokens > 0:
            categories.append(ContextCategory(
                name="Custom agents",
                tokens=agent_tokens,
                color="permission",
            ))
        
        # 5. 记忆文件
        memory_details, memory_tokens = await self.count_memory_file_tokens(memory_files)
        if memory_tokens > 0:
            categories.append(ContextCategory(
                name="Memory files",
                tokens=memory_tokens,
                color="claude",
            ))
        
        # 6. 技能
        skill_tokens = sum(self.estimate_tokens(json.dumps(s)) for s in skills)
        if skill_tokens > 0:
            categories.append(ContextCategory(
                name="Skills",
                tokens=skill_tokens,
                color="warning",
            ))
        
        # 7. 消息
        message_breakdown = await self.count_message_tokens(messages)
        message_tokens = (
            message_breakdown.tool_call_tokens +
            message_breakdown.tool_result_tokens +
            message_breakdown.assistant_message_tokens +
            message_breakdown.user_message_tokens +
            message_breakdown.attachment_tokens
        )
        if message_tokens > 0:
            categories.append(ContextCategory(
                name="Messages",
                tokens=message_tokens,
                color="purple_FOR_SUBAGENTS_ONLY",
            ))
        
        # 计算实际使用量（不含deferred）
        actual_usage = sum(
            c.tokens for c in categories if not c.is_deferred
        )
        
        # 计算free space
        reserved = 3000  # 预留空间
        free_tokens = max(0, self.context_window - actual_usage - reserved)
        
        categories.append(ContextCategory(
            name="Free space",
            tokens=free_tokens,
            color="promptBorder",
        ))
        
        # 计算总量
        total_tokens = actual_usage
        if api_usage:
            total_tokens = (
                api_usage.get("input_tokens", 0) +
                api_usage.get("cache_creation_input_tokens", 0) +
                api_usage.get("cache_read_input_tokens", 0)
            )
        
        # 构建网格
        grid_rows = self.build_grid(categories, terminal_width)
        
        # 构建结果
        return ContextData(
            categories=categories,
            total_tokens=total_tokens,
            max_tokens=self.context_window,
            raw_max_tokens=self.context_window,
            percentage=round((total_tokens / self.context_window) * 100),
            grid_rows=grid_rows,
            model=self.model,
            memory_files=memory_details,
            mcp_tools=[
                McpTool(
                    name=t.get("name", ""),
                    server_name=t.get("serverName", ""),
                    tokens=t.get("tokens", 0),
                    is_loaded=t.get("isLoaded", True),
                )
                for t in mcp_tools
            ],
            message_breakdown=message_breakdown,
            api_usage=ApiUsage(
                input_tokens=api_usage.get("input_tokens", 0) if api_usage else 0,
                output_tokens=api_usage.get("output_tokens", 0) if api_usage else 0,
                cache_creation_input_tokens=api_usage.get("cache_creation_input_tokens", 0) if api_usage else 0,
                cache_read_input_tokens=api_usage.get("cache_read_input_tokens", 0) if api_usage else 0,
            ) if api_usage else None,
        )


# 便捷函数
async def analyze_context(
    system_prompt: str,
    messages: list[dict],
    tools: Optional[list[dict]] = None,
    memory_files: Optional[list[dict]] = None,
    api_usage: Optional[dict] = None,
) -> dict:
    """
    快捷函数：分析上下文使用
    
    Returns:
        上下文分析结果字典
    """
    analyzer = ContextAnalyzer()
    
    result = await analyzer.analyze(
        system_prompt=system_prompt,
        messages=messages,
        tools=tools or [],
        memory_files=memory_files or [],
        mcp_tools=[],
        agents=[],
        skills=[],
        api_usage=api_usage,
    )
    
    return result.to_dict()


# 导出
__all__ = [
    "ContextAnalyzer",
    "ContextData",
    "ContextCategory",
    "GridSquare",
    "MemoryFile",
    "McpTool",
    "SkillInfo",
    "MessageBreakdown",
    "ApiUsage",
    "TOOL_TOKEN_COUNT_OVERHEAD",
    "CONTEXT_WINDOW_200K",
    "CONTEXT_WINDOW_1M",
    "analyze_context",
]
