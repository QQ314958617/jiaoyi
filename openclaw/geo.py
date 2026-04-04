"""
Geo - 地理工具
基于 Claude Code geo.ts 设计

地理和几何工具。
"""
import math
from typing import Tuple


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    两点间距离
    
    Args:
        x1, y1: 点1坐标
        x2, y2: 点2坐标
        
    Returns:
        距离
    """
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def manhattan_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    曼哈顿距离
    
    Args:
        x1, y1: 点1坐标
        x2, y2: 点2坐标
        
    Returns:
        曼哈顿距离
    """
    return abs(x2 - x1) + abs(y2 - y1)


def chebyshev_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    切比雪夫距离
    
    Args:
        x1, y1: 点1坐标
        x2, y2: 点2坐标
        
    Returns:
        切比雪夫距离
    """
    return max(abs(x2 - x1), abs(y2 - y1))


def midpoint(x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float]:
    """
    中点
    
    Args:
        x1, y1: 点1坐标
        x2, y2: 点2坐标
        
    Returns:
        (x, y) 中点坐标
    """
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def angle(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    两点间角度(弧度)
    
    Args:
        x1, y1: 点1坐标
        x2, y2: 点2坐标
        
    Returns:
        角度(弧度)
    """
    return math.atan2(y2 - y1, x2 - x1)


def angle_degrees(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    两点间角度(度)
    
    Args:
        x1, y1: 点1坐标
        x2, y2: 点2坐标
        
    Returns:
        角度(度)
    """
    return math.degrees(angle(x1, y1, x2, y2))


def point_in_circle(px: float, py: float, cx: float, cy: float, r: float) -> bool:
    """
    点是否在圆内
    
    Args:
        px, py: 点坐标
        cx, cy: 圆心坐标
        r: 半径
        
    Returns:
        是否在圆内
    """
    return distance(px, py, cx, cy) <= r


def point_in_rect(px: float, py: float, rx: float, ry: float, rw: float, rh: float) -> bool:
    """
    点是否在矩形内
    
    Args:
        px, py: 点坐标
        rx, ry: 矩形左上角坐标
        rw, rh: 矩形宽高
        
    Returns:
        是否在矩形内
    """
    return rx <= px <= rx + rw and ry <= py <= ry + rh


def rect_intersects(r1x: float, r1y: float, r1w: float, r1h: float,
                    r2x: float, r2y: float, r2w: float, r2h: float) -> bool:
    """
    两矩形是否相交
    
    Returns:
        是否相交
    """
    return not (r1x + r1w < r2x or r2x + r2w < r1x or
               r1y + r1h < r2y or r2y + r2h < r1y)


def lerp_point(x1: float, y1: float, x2: float, y2: float, t: float) -> Tuple[float, float]:
    """
    点线性插值
    
    Args:
        x1, y1: 起点
        x2, y2: 终点
        t: 插值因子(0-1)
        
    Returns:
        (x, y) 插值点
    """
    return (x1 + (x2 - x1) * t, y1 + (y2 - y1) * t)


def closest_point_on_line(px: float, py: float,
                           x1: float, y1: float,
                           x2: float, y2: float) -> Tuple[float, float]:
    """
    点到线段的最短距离点
    
    Returns:
        (x, y) 最近点坐标
    """
    dx = x2 - x1
    dy = y2 - y1
    
    if dx == 0 and dy == 0:
        return (x1, y1)
    
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    
    return (x1 + t * dx, y1 + t * dy)


# 导出
__all__ = [
    "distance",
    "manhattan_distance",
    "chebyshev_distance",
    "midpoint",
    "angle",
    "angle_degrees",
    "point_in_circle",
    "point_in_rect",
    "rect_intersects",
    "lerp_point",
    "closest_point_on_line",
]
