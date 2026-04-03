"""
OpenClaw Cost Tracker
=====================
Inspired by Claude Code's cost-tracker.ts (323 lines).

核心功能：
1. Token 消耗追踪（input / output / cache）
2. API 调用耗时追踪
3. 成本计算（按模型单价）
4. 会话级别成本聚合
5. 格式化输出（成本/耗时/Token数）

Claude Code 的设计：
- getTotalCostUSD() / getTotalDuration() — 全局累计
- calculateUSDCost(model, usage) — 按模型计价
- getModelUsage() — 模型维度的用量
- formatCost() / formatTotalCost() — 格式化展示
- saveCurrentSessionCosts() — 持久化到项目配置

我们的落地：
- 交易分析 API 调用成本追踪
- 每日/每周/每月成本报表
- Star Office UI 成本展示
"""

from __future__ import annotations

import os
import time
import json
import threading
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone, timedelta
from enum import Enum


# ============================================================================
# 模型单价（单位：美元/百万Token）
# ============================================================================

# MiniMax 定价（参考价，实际以官网为准）
MINIMAX_COSTS = {
    "abab6.5s-chat": {
        "input": 0.1,      # $/M tokens
        "output": 0.1,
        "cache_read": 0.01,
        "cache_write": 0.1,
    },
    "abab6.5-chat": {
        "input": 0.1,
        "output": 0.1,
        "cache_read": 0.01,
        "cache_write": 0.1,
    },
    "MiniMax-Text-01": {
        "input": 0.5,
        "output": 0.5,
        "cache_read": 0.05,
        "cache_write": 0.5,
    },
}


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class ModelUsage:
    """单个模型的 Token 用量"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    api_calls: int = 0
    total_duration_ms: int = 0


@dataclass
class APICallRecord:
    """单次 API 调用记录"""
    timestamp: float
    model: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    cost_usd: float
    success: bool
    error: Optional[str] = None


@dataclass
class CostState:
    """全局成本状态"""
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read_tokens: int = 0
    total_cache_write_tokens: int = 0
    total_api_calls: int = 0
    total_duration_ms: int = 0
    total_lines_added: int = 0
    total_lines_removed: int = 0
    model_usage: Dict[str, Dict] = field(default_factory=dict)
    web_search_requests: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cache_read_tokens": self.total_cache_read_tokens,
            "total_cache_write_tokens": self.total_cache_write_tokens,
            "total_api_calls": self.total_api_calls,
            "total_duration_ms": self.total_duration_ms,
            "total_duration_str": format_duration(self.total_duration_ms),
            "model_usage": self.model_usage,
        }


# ============================================================================
# 全局成本状态
# ============================================================================

_cost_state = CostState()
_cost_lock = threading.RLock()
_call_records: List[APICallRecord] = []  # 最近N条记录
_MAX_RECORDS = 100


# ============================================================================
# 工具函数
# ============================================================================

def format_duration(ms: int) -> str:
    """格式化时长"""
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms/1000:.1f}s"
    elif ms < 3600000:
        return f"{ms/60000:.1f}m"
    else:
        return f"{ms/3600000:.1f}h"


def format_number(n: int) -> str:
    """格式化数字（带千分位）"""
    return f"{n:,}"


def format_cost(cost: float, max_decimals: int = 4) -> str:
    """格式化成本（美元）"""
    if cost < 0.0001:
        return f"${cost * 1_000_000:.2f}μ"
    elif cost < 1:
        return f"${cost * 1000:.4f}m"
    else:
        return f"${cost:.4f}"


def format_tokens(tokens: int) -> str:
    """格式化 Token 数量"""
    if tokens < 1000:
        return str(tokens)
    elif tokens < 1_000_000:
        return f"{tokens/1000:.1f}K"
    else:
        return f"{tokens/1_000_000:.2f}M"


# ============================================================================
# 成本计算
# ============================================================================

def calculate_usd_cost(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """
    计算 API 调用的美元成本。

    对应 Claude Code 的 calculateUSDCost()。
    """
    costs = MINIMAX_COSTS.get(model, {
        "input": 0.1,
        "output": 0.1,
        "cache_read": 0.01,
        "cache_write": 0.1,
    })

    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    cache_read_cost = (cache_read_tokens / 1_000_000) * costs["cache_read"]
    cache_write_cost = (cache_write_tokens / 1_000_000) * costs["cache_write"]

    return input_cost + output_cost + cache_read_cost + cache_write_cost


# ============================================================================
# 核心追踪函数
# ============================================================================

def record_api_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    success: bool = True,
    error: Optional[str] = None,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """
    记录一次 API 调用。

    对应 Claude Code 的 addToTotalSessionCost()。

    Returns:
        本次调用的美元成本
    """
    cost = calculate_usd_cost(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
    )

    record = APICallRecord(
        timestamp=time.time(),
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=duration_ms,
        cost_usd=cost,
        success=success,
        error=error,
    )

    with _cost_lock:
        global _cost_state, _call_records

        # 更新全局状态
        _cost_state.total_cost_usd += cost
        _cost_state.total_input_tokens += input_tokens
        _cost_state.total_output_tokens += output_tokens
        _cost_state.total_cache_read_tokens += cache_read_tokens
        _cost_state.total_cache_write_tokens += cache_write_tokens
        _cost_state.total_api_calls += 1
        _cost_state.total_duration_ms += duration_ms

        # 更新模型维度
        if model not in _cost_state.model_usage:
            _cost_state.model_usage[model] = ModelUsage().__dict__
        mu = _cost_state.model_usage[model]
        mu["input_tokens"] += input_tokens
        mu["output_tokens"] += output_tokens
        mu["cache_read_tokens"] += cache_read_tokens
        mu["cache_write_tokens"] += cache_write_tokens
        mu["api_calls"] += 1
        mu["total_duration_ms"] += duration_ms

        # 记录到历史
        _call_records.append(record)
        if len(_call_records) > _MAX_RECORDS:
            _call_records.pop(0)

    return cost


def record_trade_analysis(lines_added: int = 0, lines_removed: int = 0) -> None:
    """记录交易分析（代码行数变化）"""
    with _cost_lock:
        global _cost_state
        _cost_state.total_lines_added += lines_added
        _cost_state.total_lines_removed += lines_removed


# ============================================================================
# 查询函数
# ============================================================================

def get_total_cost() -> float:
    """获取累计成本（美元）"""
    with _cost_lock:
        return _cost_state.total_cost_usd


def get_cost_state() -> CostState:
    """获取完整成本状态"""
    with _cost_lock:
        return CostState(
            total_cost_usd=_cost_state.total_cost_usd,
            total_input_tokens=_cost_state.total_input_tokens,
            total_output_tokens=_cost_state.total_output_tokens,
            total_cache_read_tokens=_cost_state.total_cache_read_tokens,
            total_cache_write_tokens=_cost_state.total_cache_write_tokens,
            total_api_calls=_cost_state.total_api_calls,
            total_duration_ms=_cost_state.total_duration_ms,
            total_lines_added=_cost_state.total_lines_added,
            total_lines_removed=_cost_state.total_lines_removed,
            model_usage=dict(_cost_state.model_usage),
        )


def get_model_usage(model: Optional[str] = None) -> Dict[str, Any]:
    """获取模型维度的用量"""
    with _cost_lock:
        if model:
            return _cost_state.model_usage.get(model, ModelUsage().__dict__)
        return dict(_cost_state.model_usage)


def get_recent_calls(limit: int = 10) -> List[Dict[str, Any]]:
    """获取最近 N 次 API 调用"""
    with _cost_lock:
        records = list(_call_records[-limit:])
    return [
        {
            "timestamp": r.timestamp,
            "time_str": datetime.fromtimestamp(r.timestamp, tz=timezone(timedelta(hours=8))).strftime("%H:%M:%S"),
            "model": r.model,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "duration_ms": r.duration_ms,
            "cost_usd": r.cost_usd,
            "success": r.success,
            "error": r.error,
        }
        for r in records
    ]


def get_total_duration_ms() -> int:
    """获取总耗时（毫秒）"""
    with _cost_lock:
        return _cost_state.total_duration_ms


# ============================================================================
# 格式化输出
# ============================================================================

def format_total_cost() -> str:
    """格式化总成本报表"""
    state = get_cost_state()
    lines = [
        f"💰 总成本: {format_cost(state.total_cost_usd)}",
        f"📞 API调用: {state.total_api_calls} 次",
        f"⏱️ 总耗时: {format_duration(state.total_duration_ms)}",
    ]
    if state.total_input_tokens > 0 or state.total_output_tokens > 0:
        lines.append(f"📥 输入Token: {format_tokens(state.total_input_tokens)}")
        lines.append(f"📤 输出Token: {format_tokens(state.total_output_tokens)}")
    if state.total_cache_read_tokens > 0:
        lines.append(f"💾 Cache读: {format_tokens(state.total_cache_read_tokens)}")
    if state.total_cache_write_tokens > 0:
        lines.append(f"💾 Cache写: {format_tokens(state.total_cache_write_tokens)}")
    if state.total_lines_added > 0 or state.total_lines_removed > 0:
        lines.append(f"📝 代码: +{state.total_lines_added} / -{state.total_lines_removed}")
    if state.model_usage:
        lines.append("---")
        lines.append("📊 按模型:")
        for model, usage in state.model_usage.items():
            cost = calculate_usd_cost(
                model,
                usage["input_tokens"],
                usage["output_tokens"],
                usage["cache_read_tokens"],
                usage["cache_write_tokens"],
            )
            lines.append(f"  {model}: {format_cost(cost)} ({usage['api_calls']} calls)")
    return "\n".join(lines)


def get_cost_summary() -> str:
    """获取简短的成本摘要"""
    state = get_cost_state()
    if state.total_api_calls == 0:
        return "暂无成本记录"
    return (
        f"💰 {format_cost(state.total_cost_usd)} · "
        f"📞 {state.total_api_calls}次 · "
        f"📥 {format_tokens(state.total_input_tokens)} · "
        f"📤 {format_tokens(state.total_output_tokens)}"
    )


# ============================================================================
# 持久化（保存到文件）
# ============================================================================

COST_FILE = os.environ.get(
    "OPENCLAW_COST_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "cost_history.json")
)


def save_cost_state() -> None:
    """保存成本状态到文件"""
    state = get_cost_state()
    try:
        os.makedirs(os.path.dirname(COST_FILE), exist_ok=True)
        with open(COST_FILE, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save cost state: {e}")


def load_cost_state() -> bool:
    """从文件加载成本状态（启动时调用）"""
    try:
        if not os.path.exists(COST_FILE):
            return False
        with open(COST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        with _cost_lock:
            global _cost_state
            _cost_state.total_cost_usd = data.get("total_cost_usd", 0)
            _cost_state.total_input_tokens = data.get("total_input_tokens", 0)
            _cost_state.total_output_tokens = data.get("total_output_tokens", 0)
            _cost_state.total_cache_read_tokens = data.get("total_cache_read_tokens", 0)
            _cost_state.total_cache_write_tokens = data.get("total_cache_write_tokens", 0)
            _cost_state.total_api_calls = data.get("total_api_calls", 0)
            _cost_state.total_duration_ms = data.get("total_duration_ms", 0)
            _cost_state.total_lines_added = data.get("total_lines_added", 0)
            _cost_state.total_lines_removed = data.get("total_lines_removed", 0)
            _cost_state.model_usage = data.get("model_usage", {})
        return True
    except Exception:
        return False


def reset_cost_state() -> None:
    """重置成本状态（测试用）"""
    global _cost_state, _call_records
    with _cost_lock:
        _cost_state = CostState()
        _call_records = []


# ============================================================================
# 定期保存线程
# ============================================================================

_save_thread_running = False
_save_thread: Optional[threading.Thread] = None


def start_auto_save(interval_seconds: int = 60) -> None:
    """启动定期保存线程"""
    global _save_thread_running, _save_thread

    if _save_thread_running:
        return

    _save_thread_running = True

    def _save_loop():
        while _save_thread_running:
            time.sleep(interval_seconds)
            save_cost_state()

    _save_thread = threading.Thread(target=_save_loop, daemon=True)
    _save_thread.start()


def stop_auto_save() -> None:
    """停止定期保存线程"""
    global _save_thread_running
    _save_thread_running = False
