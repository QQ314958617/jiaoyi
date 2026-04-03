"""
OpenClaw Tools Package
========================
Unified tool system inspired by Claude Code's tools.ts architecture.

默认注册的工具：
- PortfolioTool: 账户+持仓查询
- TradeTool: 买卖下单
- MarketTool: 市场行情
- ReviewTool: 复盘记录
"""

from openclaw.tools.registry import (
    BaseTool,
    ToolMetadata,
    ToolResult,
    ToolRegistry,
    tool_registry,
    register_tool,
    TOOL_CATEGORIES,
)

# 自动发现所有工具
tool_registry.auto_discover(__name__)
