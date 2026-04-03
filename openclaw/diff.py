"""
OpenClaw Data Diff
===================
Inspired by Claude Code's diff utilities + trading system needs.

核心功能：
1. 数据结构 diff（持仓变化、价格变化）
2. 持仓对比（上次 vs 当前）
3. 列表 diff（新增/删除/修改）
4. 变更摘要生成

交易系统用途：
- 持仓变化检测（谁加了仓、谁减了仓）
- 价格变化追踪（涨跌了多少）
- 每日状态快照对比
- 操作记录 diff
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
from collections import defaultdict


# ============================================================================
# 变更类型
# ============================================================================

class ChangeType(str, Enum):
    """变更类型"""
    ADDED = "added"        # 新增
    REMOVED = "removed"    # 删除
    MODIFIED = "modified"   # 修改
    UNCHANGED = "unchanged" # 未变


# ============================================================================
# 变更记录
# ============================================================================

@dataclass
class Change:
    """单个变更"""
    path: str           # 变更路径，如 "positions.600362.shares"
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None
    diff: Any = None    # 变化量（new - old）


@dataclass
class DiffResult:
    """Diff 结果"""
    changes: List[Change] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)  # {added: N, removed: N, modified: N}
    timestamp: float = field(default_factory=time.time)

    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def by_type(self, change_type: ChangeType) -> List[Change]:
        return [c for c in self.changes if c.change_type == change_type]

    def summary_text(self) -> str:
        """生成可读摘要"""
        parts = []
        added = self.by_type(ChangeType.ADDED)
        removed = self.by_type(ChangeType.REMOVED)
        modified = self.by_type(ChangeType.MODIFIED)

        if added:
            parts.append(f"+{len(added)} 新增")
        if removed:
            parts.append(f"-{len(removed)} 删除")
        if modified:
            parts.append(f"~{len(modified)} 修改")

        return ", ".join(parts) if parts else "无变化"


# ============================================================================
# 递归 Diff
# ============================================================================

def deep_diff(
    old: Any,
    new: Any,
    path: str = "",
    ignore_keys: Optional[set] = None,
    numeric_tolerance: float = 0.001,
) -> DiffResult:
    """
    深度对比两个数据对象。

    对应 Claude Code 的结构化 diff 逻辑。

    Args:
        old: 旧数据
        new: 新数据
        path: 当前路径（用于递归）
        ignore_keys: 忽略的字段（如 timestamp, updated_at）
        numeric_tolerance: 数值比较的容差

    Returns:
        DiffResult
    """
    changes: List[Change] = []
    ignore = ignore_keys or set()

    # 处理字典
    if isinstance(old, dict) and isinstance(new, dict):
        all_keys = set(old.keys()) | set(new.keys())
        for key in all_keys:
            if key in ignore:
                continue

            key_path = f"{path}.{key}" if path else key
            old_val = old.get(key)
            new_val = new.get(key)

            if key not in old:
                changes.append(Change(
                    path=key_path,
                    change_type=ChangeType.ADDED,
                    old_value=None,
                    new_value=new_val,
                ))
            elif key not in new:
                changes.append(Change(
                    path=key_path,
                    change_type=ChangeType.REMOVED,
                    old_value=old_val,
                    new_value=None,
                ))
            else:
                sub_changes = deep_diff(
                    old_val, new_val, key_path,
                    ignore_keys=ignore,
                    numeric_tolerance=numeric_tolerance
                ).changes
                changes.extend(sub_changes)

    # 处理列表（持仓列表等）
    elif isinstance(old, list) and isinstance(new, list):
        # 对于持仓列表，按 ID/Code 对比
        if old and new and all(isinstance(x, dict) for x in old + new):
            # 尝试找 key 字段
            key_field = None
            for candidate in ["code", "id", "stock_code", "name"]:
                if all(candidate in x for x in old + new):
                    key_field = candidate
                    break

            if key_field:
                old_map = {x[key_field]: x for x in old}
                new_map = {x[key_field]: x for x in new}

                all_keys = set(old_map.keys()) | set(new_map.keys())

                for key in all_keys:
                    key_path = f"{path}[{key}]" if path else f"[{key}]"
                    if key not in old_map:
                        changes.append(Change(
                            path=key_path,
                            change_type=ChangeType.ADDED,
                            old_value=None,
                            new_value=new_map[key],
                        ))
                    elif key not in new_map:
                        changes.append(Change(
                            path=key_path,
                            change_type=ChangeType.REMOVED,
                            old_value=old_map[key],
                            new_value=None,
                        ))
                    else:
                        sub_changes = deep_diff(
                            old_map[key], new_map[key], key_path,
                            ignore_keys=ignore,
                            numeric_tolerance=numeric_tolerance
                        ).changes
                        changes.extend(sub_changes)
            else:
                # 按位置对比
                max_len = max(len(old), len(new))
                for i in range(max_len):
                    key_path = f"{path}[{i}]"
                    old_val = old[i] if i < len(old) else None
                    new_val = new[i] if i < len(new) else None
                    if old_val is None:
                        changes.append(Change(
                            path=key_path, change_type=ChangeType.ADDED,
                            old_value=None, new_value=new_val
                        ))
                    elif new_val is None:
                        changes.append(Change(
                            path=key_path, change_type=ChangeType.REMOVED,
                            old_value=old_val, new_value=None
                        ))
                    else:
                        sub_changes = deep_diff(
                            old_val, new_val, key_path,
                            ignore_keys=ignore,
                            numeric_tolerance=numeric_tolerance
                        ).changes
                        changes.extend(sub_changes)
        else:
            # 普通列表，直接对比
            if old != new:
                changes.append(Change(
                    path=path or "list",
                    change_type=ChangeType.MODIFIED,
                    old_value=old,
                    new_value=new,
                ))

    # 处理数值（带容差）
    elif isinstance(old, (int, float)) and isinstance(new, (int, float)):
        if abs(old - new) > numeric_tolerance:
            changes.append(Change(
                path=path or "value",
                change_type=ChangeType.MODIFIED,
                old_value=old,
                new_value=new,
                diff=new - old,
            ))

    # 其他类型直接对比
    elif old != new:
        changes.append(Change(
            path=path or "value",
            change_type=ChangeType.MODIFIED,
            old_value=old,
            new_value=new,
        ))

    # 统计
    summary = {
        "added": sum(1 for c in changes if c.change_type == ChangeType.ADDED),
        "removed": sum(1 for c in changes if c.change_type == ChangeType.REMOVED),
        "modified": sum(1 for c in changes if c.change_type == ChangeType.MODIFIED),
    }

    return DiffResult(changes=changes, summary=summary)


# ============================================================================
# 持仓专用 Diff
# ============================================================================

def diff_positions(
    old_positions: Dict[str, Dict],
    new_positions: Dict[str, Dict],
) -> DiffResult:
    """
    对比持仓变化。

    专门处理交易系统的持仓数据结构。

    Args:
        old_positions: {stock_code: {shares, avg_cost, current_price, ...}}
        new_positions: 同上

    Returns:
        DiffResult，包含：
        - 新增的持仓
        - 删除的持仓
        - 修改的持仓（股数/成本/现价变化）
    """
    IGNORE = {"updated_at", "last_updated"}

    return deep_diff(
        old_positions,
        new_positions,
        path="positions",
        ignore_keys=IGNORE,
        numeric_tolerance=0.01,
    )


def format_position_change(change: Change) -> str:
    """格式化持仓变更描述"""
    path = change.path
    if change.change_type == ChangeType.ADDED:
        code = path.split("[")[-1].rstrip("]")
        val = change.new_value or {}
        shares = val.get("shares", 0)
        return f"➕ 新增 {code}: {shares}股 @ ¥{val.get('avg_cost', 0):.2f}"
    elif change.change_type == ChangeType.REMOVED:
        code = path.split("[")[-1].rstrip("]")
        val = change.old_value or {}
        shares = val.get("shares", 0)
        return f"➖ 清仓 {code}: {shares}股"
    elif change.change_type == ChangeType.MODIFIED:
        code = path.split("[")[-1].split("]")[0]
        # 找具体字段
        field_name = path.split(".")[-1] if "." in path else "value"
        if change.diff is not None:
            if field_name == "shares":
                return f"📊 {code} 股数: {int(change.old_value)} → {int(change.new_value)} ({int(change.diff):+d})"
            elif field_name == "current_price":
                return f"💹 {code} 现价: ¥{change.old_value:.2f} → ¥{change.new_value:.2f}"
            elif field_name == "avg_cost":
                return f"📝 {code} 成本: ¥{change.old_value:.2f} → ¥{change.new_value:.2f}"
            else:
                return f"~{code}.{field_name}: {change.old_value} → {change.new_value}"
        else:
            return f"~{code}.{field_name}: {change.old_value} → {change.new_value}"
    return ""


def diff_positions_summary(old: Dict, new: Dict) -> str:
    """生成持仓变化摘要"""
    result = diff_positions(old, new)

    if not result.has_changes():
        return "📊 持仓无变化"

    lines = ["📊 持仓变化："]
    for change in result.changes:
        line = format_position_change(change)
        if line:
            lines.append(f"  {line}")

    return "\n".join(lines)


# ============================================================================
# 账户状态 Diff
# ============================================================================

def diff_account_state(
    old: Dict,
    new: Dict,
) -> DiffResult:
    """
    对比账户状态变化。

    包含现金、市值、盈亏等。
    """
    IGNORE = {"updated_at", "last_updated", "timestamp"}

    return deep_diff(old, new, ignore_keys=IGNORE, numeric_tolerance=0.01)


def format_account_change(change: Change) -> str:
    """格式化账户变更"""
    field = change.path.split(".")[-1]

    if change.diff is not None:
        if field == "cash":
            return f"💰 现金: ¥{change.old_value:,.0f} → ¥{change.new_value:,.0f} ({change.diff:+,.0f})"
        elif field == "total_value":
            return f"📈 总市值: ¥{change.old_value:,.0f} → ¥{change.new_value:,.0f} ({change.diff:+,.0f})"
        elif field == "pnl" or "profit" in field.lower():
            return f"💵 盈亏: ¥{change.old_value:+,.0f} → ¥{change.new_value:+,.0f} ({change.diff:+,.0f})"

    return f"  {field}: {change.old_value} → {change.new_value}"


def diff_account_summary(old: Dict, new: Dict) -> str:
    """生成账户变化摘要"""
    result = diff_account_state(old, new)

    if not result.has_changes():
        return "💼 账户无变化"

    lines = ["💼 账户变化："]
    for change in result.changes:
        line = format_account_change(change)
        if line:
            lines.append(f"  {line}")

    return "\n".join(lines)


# ============================================================================
# 便捷函数
# ============================================================================

def compare(old: Any, new: Any) -> DiffResult:
    """
    快速对比两个对象。

    用法：
        result = compare(old_positions, new_positions)
        if result.has_changes():
            print(result.summary_text())
    """
    return deep_diff(old, new)


def changed(old: Any, new: Any) -> bool:
    """快速检查是否有变化"""
    return deep_diff(old, new).has_changes()
