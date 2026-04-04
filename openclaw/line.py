"""
Line - 线条
基于 Claude Code line.ts 设计

线条和边界工具。
"""
import math
from typing import Optional, Tuple


class Line:
    """
    线条
    
    表示两点之间的线段。
    """
    
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        """
        Args:
            x1, y1: 起点
            x2, y2: 终点
        """
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
    
    @property
    def length(self) -> float:
        """线段长度"""
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        return math.sqrt(dx * dx + dy * dy)
    
    @property
    def angle(self) -> float:
        """线段角度(弧度)"""
        return math.atan2(self.y2 - self.y1, self.x2 - self.x1)
    
    @property
    def midpoint(self) -> Tuple[float, float]:
        """中点"""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    def distance_to_point(self, px: float, py: float) -> float:
        """点到线段的距离"""
        dx = self.x2 - self.x1
        dy = self.y2 - self.y1
        
        if dx == 0 and dy == 0:
            return math.sqrt((px - self.x1) ** 2 + (py - self.y1) ** 2)
        
        t = max(0, min(1, ((px - self.x1) * dx + (py - self.y1) * dy) / (dx * dx + dy * dy)))
        
        near_x = self.x1 + t * dx
        near_y = self.y1 + t * dy
        
        return math.sqrt((px - near_x) ** 2 + (py - near_y) ** 2)


class Rect:
    """
    矩形
    
    表示轴对齐矩形。
    """
    
    def __init__(self, x: float, y: float, width: float, height: float):
        """
        Args:
            x, y: 左上角坐标
            width: 宽度
            height: 高度
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def left(self) -> float:
        return self.x
    
    @property
    def top(self) -> float:
        return self.y
    
    @property
    def right(self) -> float:
        return self.x + self.width
    
    @property
    def bottom(self) -> float:
        return self.y + self.height
    
    @property
    def center(self) -> Tuple[float, float]:
        """中心点"""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def area(self) -> float:
        """面积"""
        return self.width * self.height
    
    def contains_point(self, px: float, py: float) -> bool:
        """点是否在矩形内"""
        return self.left <= px <= self.right and self.top <= py <= self.bottom
    
    def intersects(self, other: "Rect") -> bool:
        """是否与另一个矩形相交"""
        return not (self.right < other.left or other.right < self.left or
                   self.bottom < other.top or other.bottom < self.top)
    
    def union(self, other: "Rect") -> "Rect":
        """并集矩形"""
        x = min(self.left, other.left)
        y = min(self.top, other.top)
        r = max(self.right, other.right)
        b = max(self.bottom, other.bottom)
        return Rect(x, y, r - x, b - y)
    
    def intersection(self, other: "Rect") -> Optional["Rect"]:
        """交集矩形"""
        if not self.intersects(other):
            return None
        
        x = max(self.left, other.left)
        y = max(self.top, other.top)
        r = min(self.right, other.right)
        b = min(self.bottom, other.bottom)
        
        return Rect(x, y, r - x, b - y)


class Circle:
    """
    圆
    """
    
    def __init__(self, cx: float, cy: float, r: float):
        """
        Args:
            cx, cy: 圆心
            r: 半径
        """
        self.cx = cx
        self.cy = cy
        self.r = r
    
    @property
    def diameter(self) -> float:
        return self.r * 2
    
    @property
    def area(self) -> float:
        return math.pi * self.r ** 2
    
    def contains_point(self, px: float, py: float) -> bool:
        """点是否在圆内"""
        dx = px - self.cx
        dy = py - self.cy
        return dx * dx + dy * dy <= self.r * self.r
    
    def intersects(self, other: "Circle") -> bool:
        """是否与另一个圆相交"""
        dx = other.cx - self.cx
        dy = other.cy - self.cy
        dist_sq = dx * dx + dy * dy
        return dist_sq <= (self.r + other.r) ** 2


# 导出
__all__ = [
    "Line",
    "Rect",
    "Circle",
]
