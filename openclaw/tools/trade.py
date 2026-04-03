"""
OpenClaw Trade Tools
====================
基于 BaseTool 架构的交易相关工具。
"""

from typing import Any, Dict, Optional
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from openclaw.tools.base import (
    BaseTool, ToolContext, ToolResult, ToolCategory,
    register_tool, tool_registry,
)


# ============================================================================
# 工具1：获取账户和持仓
# ============================================================================

class PortfolioTool(BaseTool):
    """
    获取账户和持仓信息。

    类似于 app.py 的 /api/portfolio。
    只读操作。
    """
    name = "portfolio"
    description = "获取当前账户余额、持仓情况和盈亏状态"
    category = ToolCategory.TRADING
    tags = {"account", "positions", "balance"}

    def is_read_only(self, input_data: Optional[Dict] = None) -> bool:
        return True

    def get_activity_description(self, input_data: Optional[Dict]) -> str:
        return "Getting portfolio information"

    def validate_input(self, input_data: Dict) -> Optional[ToolResult]:
        return None

    def call(self, ctx: ToolContext, input_data: Dict) -> ToolResult:
        try:
            # 延迟导入避免循环
            import database as db
            import akshare as ak

            portfolio = db.get_portfolio()

            # 获取持仓成本和现价计算盈亏
            positions_data = []
            total_cost = 0
            total_value = 0

            for code, pos in portfolio.get("positions", {}).items():
                cost = pos.get("cost", 0)
                shares = pos.get("shares", 0)
                avg_cost = cost / shares if shares > 0 else 0
                total_cost += cost
                positions_data.append({
                    "code": code,
                    "name": pos.get("name", code),
                    "shares": shares,
                    "avg_cost": round(avg_cost, 3),
                    "cost": cost,
                })

            result = {
                "cash": portfolio.get("cash", 0),
                "total_value": portfolio.get("total_value", 0),
                "total_profit": portfolio.get("total_profit", 0),
                "positions": positions_data,
            }

            return ToolResult.success_result(
                data=result,
                summary=f"账户现金 {result['cash']} 元，持仓 {len(positions_data)} 只",
            )

        except Exception as e:
            return ToolResult.error_result(error=str(e))


# ============================================================================
# 工具2：获取交易记录
# ============================================================================

class TradesTool(BaseTool):
    """获取交易历史记录"""
    name = "trades"
    description = "获取最近的交易买卖历史记录"
    category = ToolCategory.TRADING
    tags = {"history", "trades"}

    def is_read_only(self, input_data: Optional[Dict] = None) -> bool:
        return True

    def validate_input(self, input_data: Dict) -> Optional[ToolResult]:
        return None

    def call(self, ctx: ToolContext, input_data: Dict) -> ToolResult:
        try:
            import database as db

            limit = input_data.get("limit", 20)
            trades = db.get_trades(limit=limit)

            return ToolResult.success_result(
                data={"trades": trades, "count": len(trades)},
                summary=f"最近 {len(trades)} 条交易记录",
            )

        except Exception as e:
            return ToolResult.error_result(error=str(e))


# ============================================================================
# 工具3：执行买卖交易
# ============================================================================

class TradeTool(BaseTool):
    """
    执行股票买卖交易。

    有破坏性操作（修改持仓）。
    需要权限确认。
    """
    name = "trade"
    description = "执行股票买入或卖出操作，需要指定股票代码、买卖方向和股数"
    category = ToolCategory.TRADING
    tags = {"buy", "sell", "execute"}

    def is_read_only(self, input_data: Optional[Dict] = None) -> bool:
        return False

    def is_destructive(self, input_data: Optional[Dict] = None) -> bool:
        return input_data.get("action") == "sell" if input_data else False

    def get_activity_description(self, input_data: Optional[Dict]) -> Optional[str]:
        action = input_data.get("action", "") if input_data else ""
        code = input_data.get("stock_code", "") if input_data else ""
        shares = input_data.get("shares", 0) if input_data else 0
        return f"{'Buying' if action == 'buy' else 'Selling'} {shares} shares of {code}" if code else None

    def validate_input(self, input_data: Dict) -> Optional[ToolResult]:
        """验证交易参数"""
        if input_data.get("action") not in ("buy", "sell"):
            return ToolResult.error_result(
                error="action must be 'buy' or 'sell'"
            )
        if not input_data.get("stock_code"):
            return ToolResult.error_result(error="stock_code is required")
        shares = input_data.get("shares", 0)
        if not isinstance(shares, int) or shares <= 0:
            return ToolResult.error_result(error="shares must be a positive integer")
        if shares % 100 != 0:
            return ToolResult.error_result(error="shares must be a multiple of 100 (手)")
        return None

    def call(self, ctx: ToolContext, input_data: Dict) -> ToolResult:
        try:
            import database as db
            import json

            action = input_data["action"]
            stock_code = input_data["stock_code"]
            shares = input_data["shares"]
            reason = input_data.get("reason", "")

            # 调用 Flask app 的交易接口（通过内联调用避免网络开销）
            from app import execute_trade as app_execute_trade

            result = app_execute_trade(action, stock_code, shares, reason)
            return ToolResult.success_result(data=result)

        except Exception as e:
            return ToolResult.error_result(error=str(e))


# ============================================================================
# 工具4：获取大盘指数
# ============================================================================

class IndexTool(BaseTool):
    """获取上证指数和均线数据"""
    name = "index"
    description = "获取上证指数当前价格、MA5/MA10均线，判断是否多头排列"
    category = ToolCategory.MARKET
    tags = {"index", "market", "ma5", "ma10"}

    def is_read_only(self, input_data: Optional[Dict] = None) -> bool:
        return True

    def validate_input(self, input_data: Dict) -> Optional[ToolResult]:
        return None

    def get_activity_description(self, input_data: Optional[Dict]) -> str:
        return "Getting market index data"

    def call(self, ctx: ToolContext, input_data: Dict) -> ToolResult:
        try:
            from app import get_index_data

            data = get_index_data()

            # 格式化摘要
            status = []
            if data.get("above_ma5"):
                status.append("站上MA5")
            if data.get("ma5_above_ma10"):
                status.append("MA5>MA10多头")
            summary = "、".join(status) if status else "偏弱"

            return ToolResult.success_result(
                data=data,
                summary=f"上证 {data.get('price')} ({data.get('change_pct', 0):+.2f}%)，{summary}",
            )

        except Exception as e:
            return ToolResult.error_result(error=str(e))


# ============================================================================
# 工具5：获取股票行情
# ============================================================================

class QuoteTool(BaseTool):
    """获取单只或多只股票实时行情"""
    name = "quote"
    description = "获取股票实时价格、涨跌幅、成交量等行情数据"
    category = ToolCategory.MARKET
    tags = {"quote", "price", "realtime"}

    def is_read_only(self, input_data: Optional[Dict] = None) -> bool:
        return True

    def validate_input(self, input_data: Dict) -> Optional[ToolResult]:
        if not input_data.get("stock_code"):
            return ToolResult.error_result(error="stock_code is required")
        return None

    def get_activity_description(self, input_data: Optional[Dict]) -> Optional[str]:
        code = input_data.get("stock_code", "") if input_data else ""
        return f"Getting quote for {code}" if code else None

    def call(self, ctx: ToolContext, input_data: Dict) -> ToolResult:
        try:
            from app import get_tencent_quote

            code = input_data["stock_code"]
            codes = [c.strip() for c in code.split(",")]

            quotes = get_tencent_quote(codes)
            result = []
            for c, q in quotes.items():
                result.append({
                    "code": c,
                    "name": q.get("name", ""),
                    "price": q.get("price", 0),
                    "change_pct": q.get("change_pct", 0),
                    "volume": q.get("volume", 0),
                })

            return ToolResult.success_result(
                data={"quotes": result, "count": len(result)},
                summary=f"获取 {len(result)} 只股票行情",
            )

        except Exception as e:
            return ToolResult.error_result(error=str(e))


# ============================================================================
# 工具6：获取每日复盘
# ============================================================================

class DailyReviewTool(BaseTool):
    """获取每日复盘记录"""
    name = "daily_review"
    description = "获取每日交易复盘记录，包括操作总结和明日建议"
    category = ToolCategory.REVIEW
    tags = {"review", "daily", "summary"}

    def is_read_only(self, input_data: Optional[Dict] = None) -> bool:
        return True

    def validate_input(self, input_data: Dict) -> Optional[ToolResult]:
        return None

    def call(self, ctx: ToolContext, input_data: Dict) -> ToolResult:
        try:
            import database as db

            limit = input_data.get("limit", 5)
            reviews = db.get_reviews(limit=limit)

            return ToolResult.success_result(
                data={"reviews": reviews, "count": len(reviews)},
                summary=f"最近 {len(reviews)} 条复盘",
            )

        except Exception as e:
            return ToolResult.error_result(error=str(e))


# ============================================================================
# 工具7：写入复盘
# ============================================================================

class WriteReviewTool(BaseTool):
    """写入每日复盘"""
    name = "write_review"
    description = "写入每日交易复盘内容，包含操作记录和市场分析"
    category = ToolCategory.REVIEW
    tags = {"review", "write"}

    def is_read_only(self, input_data: Optional[Dict] = None) -> bool:
        return False

    def is_destructive(self, input_data: Optional[Dict] = None) -> bool:
        return False  # 追加写入，非破坏性

    def validate_input(self, input_data: Dict) -> Optional[ToolResult]:
        if not input_data.get("content"):
            return ToolResult.error_result(error="content is required")
        return None

    def call(self, ctx: ToolContext, input_data: Dict) -> ToolResult:
        try:
            import database as db

            date = input_data.get("date")
            content = input_data["content"]
            tags = input_data.get("tags", [])
            strategies = input_data.get("strategies", [])

            if isinstance(tags, list):
                tags = ",".join(tags)
            if isinstance(strategies, list):
                strategies = ",".join(strategies)

            review_id = db.add_review(date=date, content=content, tags=tags, strategies=strategies)

            return ToolResult.success_result(
                data={"review_id": review_id},
                summary=f"复盘写入成功，id={review_id}",
            )

        except Exception as e:
            return ToolResult.error_result(error=str(e))


# ============================================================================
# 注册所有交易工具
# ============================================================================

_known_tools = [
    PortfolioTool,
    TradesTool,
    TradeTool,
    IndexTool,
    QuoteTool,
    DailyReviewTool,
    WriteReviewTool,
]

for _tool_cls in _known_tools:
    tool_registry.register(_tool_cls)
