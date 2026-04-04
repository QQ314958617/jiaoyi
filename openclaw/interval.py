"""
Interval - 区间
基于 Claude Code interval.ts 设计

区间操作工具。
"""
from typing import List, Optional, Tuple


class Interval:
    """
    区间
    
    表示数值区间。
    """
    
    def __init__(self, start: float, end: float):
        """
        Args:
            start: 起始值
            end: 结束值
        """
        if start > end:
            raise ValueError("Start must be <= end")
        
        self._start = start
        self._end = end
    
    @property
    def start(self) -> float:
        return self._start
    
    @property
    def end(self) -> float:
        return self._end
    
    @property
    def length(self) -> float:
        """区间长度"""
        return self._end - self._start
    
    def contains(self, value: float) -> bool:
        """是否包含值"""
        return self._start <= value <= self._end
    
    def contains_interval(self, other: "Interval") -> bool:
        """是否包含另一个区间"""
        return self._start <= other._start and self._end >= other._end
    
    def overlaps(self, other: "Interval") -> bool:
        """是否与另一个区间重叠"""
        return not (self._end <= other._start or other._end <= self._start)
    
    def intersection(self, other: "Interval") -> Optional["Interval"]:
        """与另一个区间的交集"""
        if not self.overlaps(other):
            return None
        
        return Interval(max(self._start, other._start), min(self._end, other._end))
    
    def union(self, other: "Interval") -> List["Interval"]:
        """与另一个区间的并集"""
        if not self.overlaps(other):
            return [self, other]
        
        return [Interval(min(self._start, other._start), max(self._end, other._end))]
    
    def equals(self, other: "Interval") -> bool:
        """是否相等"""
        return self._start == other._start and self._end == other._end
    
    def __repr__(self) -> str:
        return f"[{self._start}, {self._end}]"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Interval):
            return self.equals(other)
        return False


def merge_intervals(intervals: List[Interval]) -> List[Interval]:
    """
    合并区间列表
    
    Args:
        intervals: 区间列表
        
    Returns:
        合并后的区间列表
    """
    if not intervals:
        return []
    
    # 按起始值排序
    sorted_intervals = sorted(intervals, key=lambda i: i.start)
    
    result = [sorted_intervals[0]]
    
    for interval in sorted_intervals[1:]:
        last = result[-1]
        
        if interval.start <= last.end:
            # 重叠，合并
            new_interval = Interval(last.start, max(last.end, interval.end))
            result[-1] = new_interval
        else:
            # 不重叠，添加
            result.append(interval)
    
    return result


def is_within(value: float, start: float, end: float) -> bool:
    """检查值是否在区间内"""
    return start <= value <= end


def clamp(value: float, min_val: float, max_val: float) -> float:
    """限制值在区间内"""
    return max(min_val, min(max_val, value))


# 导出
__all__ = [
    "Interval",
    "merge_intervals",
    "is_within",
    "clamp",
]
