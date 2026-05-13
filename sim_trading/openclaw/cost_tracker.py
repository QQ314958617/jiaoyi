"""
CostTracker - 成本追踪
基于 Claude Code cost_tracker.ts 设计

成本追踪工具。
"""
from typing import Dict, Optional
from datetime import datetime


class CostTracker:
    """
    成本追踪器
    """
    
    def __init__(self):
        self._records: list = []
        self._totals: Dict[str, float] = {}
    
    def record(self, operation: str, cost: float, tokens: int = 0):
        """
        记录操作
        
        Args:
            operation: 操作名称
            cost: 成本
            tokens: Token数
        """
        self._records.append({
            "operation": operation,
            "cost": cost,
            "tokens": tokens,
            "timestamp": datetime.now().isoformat(),
        })
        
        if operation not in self._totals:
            self._totals[operation] = 0
        self._totals[operation] += cost
    
    def total(self) -> float:
        """总成本"""
        return sum(self._totals.values())
    
    def by_operation(self, operation: str) -> float:
        """按操作统计"""
        return self._totals.get(operation, 0)
    
    def records(self) -> list:
        """所有记录"""
        return list(self._records)
    
    def clear(self):
        """清空"""
        self._records = []
        self._totals = {}
    
    def summary(self) -> dict:
        """汇总"""
        return {
            "total": self.total(),
            "operations": dict(self._totals),
            "count": len(self._records),
        }


# 全局追踪器
_tracker = CostTracker()


def get_tracker() -> CostTracker:
    """获取全局追踪器"""
    return _tracker


def record(operation: str, cost: float, tokens: int = 0):
    """记录操作"""
    _tracker.record(operation, cost, tokens)


def total() -> float:
    """总成本"""
    return _tracker.total()


def summary() -> dict:
    """汇总"""
    return _tracker.summary()


def clear():
    """清空"""
    _tracker.clear()


# 导出
__all__ = [
    "CostTracker",
    "get_tracker",
    "record",
    "total",
    "summary",
    "clear",
]
