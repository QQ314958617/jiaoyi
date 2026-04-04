"""
Interval - 区间
基于 Claude Code interval.ts 设计

区间工具。
"""
from typing import List, Tuple, Union


class Interval:
    """
    区间
    
    表示一个数值区间。
    """
    
    def __init__(self, start: float, end: float, inclusive: bool = True):
        """
        Args:
            start: 起始值
            end: 结束值
            inclusive: 是否包含结束值
        """
        if start > end:
            raise ValueError(f"Invalid interval: {start} > {end}")
        
        self.start = start
        self.end = end
        self.inclusive = inclusive
    
    def contains(self, value: float) -> bool:
        """
        检查值是否在区间内
        
        Args:
            value: 值
            
        Returns:
            是否包含
        """
        if self.inclusive:
            return self.start <= value <= self.end
        return self.start <= value < self.end
    
    def overlaps(self, other: "Interval") -> bool:
        """
        检查是否与另一个区间重叠
        
        Args:
            other: 另一个区间
            
        Returns:
            是否重叠
        """
        return not (self.end < other.start or self.start > other.end)
    
    def intersection(self, other: "Interval") -> "Interval":
        """
        与另一个区间的交集
        
        Args:
            other: 另一个区间
            
        Returns:
            交集区间（无交集返回None）
        """
        if not self.overlaps(other):
            return None
        
        new_start = max(self.start, other.start)
        new_end = min(self.end, other.end)
        
        return Interval(new_start, new_end, self.inclusive and other.inclusive)
    
    def union(self, other: "Interval") -> List["Interval"]:
        """
        与另一个区间的并集
        
        Args:
            other: 另一个区间
            
        Returns:
            不重叠的区间列表
        """
        if not self.overlaps(other) and self.end < other.start - 1:
            # 不相邻也不重叠
            if self.start <= other.start:
                return [self, other]
            return [other, self]
        
        # 合并
        new_start = min(self.start, other.start)
        new_end = max(self.end, other.end)
        return [Interval(new_start, new_end, True)]
    
    def __str__(self) -> str:
        if self.inclusive:
            return f"[{self.start}, {self.end}]"
        return f"[{self.start}, {self.end})"
    
    def __repr__(self) -> str:
        return f"Interval({self.start}, {self.end}, {self.inclusive})"
    
    def __eq__(self, other: "Interval") -> bool:
        return (self.start == other.start and 
                self.end == other.end and 
                self.inclusive == other.inclusive)


def merge_intervals(intervals: List[Interval]) -> List[Interval]:
    """
    合并重叠的区间
    
    Args:
        intervals: 区间列表
        
    Returns:
        合并后的区间列表
    """
    if not intervals:
        return []
    
    # 按起始值排序
    sorted_intervals = sorted(intervals, key=lambda x: x.start)
    
    result = [sorted_intervals[0]]
    
    for current in sorted_intervals[1:]:
        last = result[-1]
        
        if current.start <= last.end + 1 and current.overlaps(last):
            new_end = max(last.end, current.end)
            result[-1] = Interval(last.start, new_end, True)
        elif current.start > last.end:
            result.append(current)
    
    return result


def get_overlaps(intervals: List[Interval]) -> List[Tuple[Interval, Interval]]:
    """
    获取所有重叠的区间对
    
    Args:
        intervals: 区间列表
        
    Returns:
        重叠的区间对列表
    """
    result = []
    n = len(intervals)
    
    for i in range(n):
        for j in range(i + 1, n):
            if intervals[i].overlaps(intervals[j]):
                result.append((intervals[i], intervals[j]))
    
    return result


# 导出
__all__ = [
    "Interval",
    "merge_intervals",
    "get_overlaps",
]
