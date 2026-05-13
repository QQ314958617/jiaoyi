"""
交易反思服务 (Reflection Service)

借鉴 QuantDinger 的 Reflection 模块，实现交易后验证和自动学习闭环。

核心流程：
1. 定期验证历史交易决策的正确性
2. 统计各策略的实际表现
3. 触发参数校准（如果表现偏离预期）
4. 生成进化建议

与 QuantDinger 的区别：
- QD 验证的是 AI 分析信号（BUY/SELL/HOLD 预测 vs 实际涨跌）
- 我们验证的是策略执行质量（是否按规则执行、止损是否及时等）
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

import database as db

logger = logging.getLogger(__name__)


class ReflectionService:
    """交易反思与自动学习"""

    def run_reflection(self, lookback_days: int = 7) -> Dict[str, Any]:
        """
        运行一次反思周期：
        1. 分析最近交易的执行质量
        2. 检查止损/止盈是否及时
        3. 统计策略表现
        4. 生成改进建议
        """
        results = {
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "lookback_days": lookback_days,
            "strategies": {},
            "overall": {},
            "issues": [],
            "improvements": [],
        }

        cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).isoformat()

        with db.get_connection() as conn:
            trades = conn.execute("""
                SELECT * FROM trades
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            """, (cutoff,)).fetchall()

        if not trades:
            results["overall"] = {"message": "无近期交易记录"}
            return results

        trades_list = [dict(t) for t in trades]

        # 按策略分组分析
        by_strategy = {}
        for t in trades_list:
            sid = t.get("strategy_id", 0)
            if sid not in by_strategy:
                by_strategy[sid] = []
            by_strategy[sid].append(t)

        for sid, strades in by_strategy.items():
            analysis = self._analyze_strategy_trades(sid, strades)
            results["strategies"][sid] = analysis

        # 整体分析
        results["overall"] = self._overall_analysis(trades_list)

        # 检查执行质量问题
        results["issues"] = self._check_execution_issues(trades_list)

        # 生成改进建议
        results["improvements"] = self._generate_improvements(results)

        # 保存反思记录
        self._save_reflection(results)

        return results

    def _analyze_strategy_trades(self, strategy_id: int, trades: List[Dict]) -> Dict[str, Any]:
        """分析单个策略的交易表现"""
        buys = [t for t in trades if t["action"] == "buy"]
        sells = [t for t in trades if t["action"] == "sell"]

        # 计算已实现盈亏
        total_profit = sum(t.get("profit", 0) or 0 for t in sells)
        win_sells = [t for t in sells if (t.get("profit", 0) or 0) > 0]
        loss_sells = [t for t in sells if (t.get("profit", 0) or 0) < 0]

        win_rate = len(win_sells) / len(sells) * 100 if sells else 0

        return {
            "strategy_id": strategy_id,
            "total_trades": len(trades),
            "buys": len(buys),
            "sells": len(sells),
            "total_profit": round(total_profit, 2),
            "win_rate": round(win_rate, 1),
            "win_count": len(win_sells),
            "loss_count": len(loss_sells),
            "avg_profit_per_trade": round(total_profit / len(sells), 2) if sells else 0,
        }

    def _overall_analysis(self, trades: List[Dict]) -> Dict[str, Any]:
        """整体交易分析"""
        sells = [t for t in trades if t["action"] == "sell"]
        total_profit = sum(t.get("profit", 0) or 0 for t in sells)
        trade_count = len(trades)

        return {
            "total_trades": trade_count,
            "total_sells": len(sells),
            "total_profit": round(total_profit, 2),
            "avg_trades_per_day": round(trade_count / 7, 1),
        }

    def _check_execution_issues(self, trades: List[Dict]) -> List[Dict[str, Any]]:
        """检查执行质量问题"""
        issues = []

        sells = [t for t in trades if t["action"] == "sell"]

        for t in sells:
            profit = t.get("profit", 0) or 0
            reason = t.get("reason", "") or ""

            # 检查大额亏损（止损可能不及时）
            if profit < -500:
                amount = t.get("amount", 0) or 0
                loss_pct = (profit / amount * 100) if amount > 0 else 0
                if loss_pct < -3:
                    issues.append({
                        "type": "late_stop_loss",
                        "severity": "high",
                        "stock_code": t["stock_code"],
                        "loss_pct": round(loss_pct, 2),
                        "profit": round(profit, 2),
                        "timestamp": t["timestamp"],
                        "message": f"{t['stock_code']} 亏损{loss_pct:.1f}%，超过-3%止损线",
                    })

            # 检查过早止盈（盈利太少就跑了）
            if 0 < profit < 100 and "止盈" in reason:
                issues.append({
                    "type": "premature_take_profit",
                    "severity": "low",
                    "stock_code": t["stock_code"],
                    "profit": round(profit, 2),
                    "timestamp": t["timestamp"],
                    "message": f"{t['stock_code']} 盈利仅¥{profit:.0f}就止盈，可能过早",
                })

        # 检查同日买卖（T+1 违规）
        buy_dates = {}
        for t in trades:
            if t["action"] == "buy":
                date = t["timestamp"][:10] if t.get("timestamp") else ""
                code = t["stock_code"]
                buy_dates[(code, date)] = True

        for t in trades:
            if t["action"] == "sell":
                date = t["timestamp"][:10] if t.get("timestamp") else ""
                code = t["stock_code"]
                if (code, date) in buy_dates:
                    issues.append({
                        "type": "t1_violation",
                        "severity": "critical",
                        "stock_code": code,
                        "timestamp": t["timestamp"],
                        "message": f"{code} 同日买卖，违反T+1规则！",
                    })

        return issues

    def _generate_improvements(self, results: Dict[str, Any]) -> List[str]:
        """基于反思结果生成改进建议"""
        improvements = []
        issues = results.get("issues", [])

        # 止损问题
        late_stops = [i for i in issues if i["type"] == "late_stop_loss"]
        if late_stops:
            improvements.append(
                f"🚨 发现{len(late_stops)}次止损不及时，建议：加强盘中监控频率，"
                f"或将止损从-2%收紧到-1.5%"
            )

        # T+1 违规
        t1_issues = [i for i in issues if i["type"] == "t1_violation"]
        if t1_issues:
            improvements.append(
                f"❌ 发现{len(t1_issues)}次T+1违规！必须在交易前检查买入日期"
            )

        # 策略表现
        for sid, analysis in results.get("strategies", {}).items():
            win_rate = analysis.get("win_rate", 0)
            if win_rate < 40:
                improvements.append(
                    f"⚠️ 策略{sid}胜率仅{win_rate:.0f}%，建议暂停并重新校准参数"
                )
            elif win_rate > 70:
                improvements.append(
                    f"✅ 策略{sid}胜率{win_rate:.0f}%，表现优秀，可考虑适当加仓"
                )

        if not improvements:
            improvements.append("✅ 近期交易执行质量良好，无明显问题")

        return improvements

    def _save_reflection(self, results: Dict[str, Any]):
        """保存反思记录到复盘表"""
        content = self._format_reflection_report(results)
        today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
        with db.get_connection() as conn:
            conn.execute("""
                INSERT INTO daily_reviews (date, content, tags, strategies)
                VALUES (?, ?, ?, ?)
            """, (
                today,
                content,
                json.dumps(["自动反思", "策略校准"], ensure_ascii=False),
                json.dumps(list(results.get("strategies", {}).keys())),
            ))

    def _format_reflection_report(self, results: Dict[str, Any]) -> str:
        """格式化反思报告"""
        lines = ["## 🔄 自动反思报告\n"]

        # 整体
        overall = results.get("overall", {})
        lines.append(f"**分析周期**: 最近{results.get('lookback_days', 7)}天")
        lines.append(f"**总交易数**: {overall.get('total_trades', 0)}")
        lines.append(f"**已实现盈亏**: ¥{overall.get('total_profit', 0):,.2f}\n")

        # 各策略
        for sid, analysis in results.get("strategies", {}).items():
            lines.append(f"### 策略{sid}")
            lines.append(f"- 交易{analysis['total_trades']}笔，胜率{analysis['win_rate']}%")
            lines.append(f"- 盈亏: ¥{analysis['total_profit']:,.2f}")
            lines.append("")

        # 问题
        issues = results.get("issues", [])
        if issues:
            lines.append("### ⚠️ 发现问题")
            for issue in issues[:5]:
                lines.append(f"- [{issue['severity']}] {issue['message']}")
            lines.append("")

        # 改进建议
        improvements = results.get("improvements", [])
        if improvements:
            lines.append("### 💡 改进建议")
            for imp in improvements:
                lines.append(f"- {imp}")

        return "\n".join(lines)


def run_weekly_reflection() -> Dict[str, Any]:
    """便捷函数：运行每周反思"""
    svc = ReflectionService()
    return svc.run_reflection(lookback_days=7)


def run_monthly_reflection() -> Dict[str, Any]:
    """便捷函数：运行每月反思"""
    svc = ReflectionService()
    return svc.run_reflection(lookback_days=30)
