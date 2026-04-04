"""
Range - 范围
基于 Claude Code range.ts 设计

数值范围工具。
"""
from typing import Generator, List


class Range:
    """
    数值范围
    
    表示一个数值区间。
    """
    
    def __init__(self, start: float, end: float, step: float = 1):
        """
        Args:
            start: 起始值
            end: 结束值
            step: 步长
        """
        self.start = start
        self.end = end
        self.step = step
    
    @property
    def length(self) -> float:
        """范围长度"""
        return self.end - self.start
    
    def contains(self, value: float) -> bool:
        """是否包含值"""
        return self.start <= value <= self.end
    
    def contains_range(self, other: "Range") -> bool:
        """是否包含另一个范围"""
        return self.start <= other.start and self.end >= other.end
    
    def overlaps(self, other: "Range") -> bool:
        """是否与另一个范围重叠"""
        return not (self.end <= other.start or other.end <= self.start)
    
    def intersection(self, other: "Range") -> "Range":
        """交集"""
        if not self.overlaps(other):
            return Range(0, 0, 1)
        
        new_start = max(self.start, other.start)
        new_end = min(self.end, other.end)
        return Range(new_start, new_end, self.step)
    
    def union(self, other: "Range") -> List["Range"]:
        """并集"""
        if not self.overlaps(other):
            return [Range(self.start, self.end, self.step),
                    Range(other.start, other.end, other.step)]
        
        new_start = min(self.start, other.start)
        new_end = max(self.end, other.end)
        return [Range(new_start, new_end, self.step)]
    
    def __iter__(self):
        """迭代"""
        value = self.start
        while value <= self.end:
            yield value
            value += self.step
    
    def __len__(self) -> int:
        """元素数量"""
        return int((self.end - self.start) / self.step) + 1
    
    def __repr__(self) -> str:
        return f"Range({self.start}, {self.end}, {self.step})"


def range_inclusive(start: int, end: int, step: int = 1) -> List[int]:
    """
    包含性range
    
    Args:
        start: 起始值(包含)
        end: 结束值(包含)
        step: 步长
        
    Returns:
        数字列表
    """
    result = []
    current = start
    
    if step > 0:
        while current <= end:
            result.append(current)
            current += step
    elif step < 0:
        while current >= end:
            result.append(current)
            current += step
    
    return result


def range_exclusive(start: int, end: int, step: int = 1) -> List[int]:
    """
    排他性range
    
    Args:
        start: 起始值(不包含)
        end: 结束值(不包含)
        step: 步长
        
    Returns:
        数字列表
    """
    return range_inclusive(start + step if step > 0 else start + step,
                          end - step if step > 0 else end + step, step)


def numeric_range(start: float, stop: float, num: int = 50) -> List[float]:
    """
    数值范围(等分)
    
    Args:
        start: 起始值
        stop: 结束值
        num: 分段数
        
    Returns:
        等分点列表
    """
    if num <= 1:
        return [start]
    
    step = (stop - start) / (num - 1)
    return [start + i * step for i in range(num)]


def clamp(value: float, min_val: float, max_val: float) -> float:
    """限制在范围内"""
    return max(min_val, min(max_val, value))


# 导出
__all__ = [
    "Range",
    "range_inclusive",
    "range_exclusive",
    "numeric_range",
    "clamp",
]
