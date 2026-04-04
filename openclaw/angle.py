"""
Angle - 角度
基于 Claude Code angle.ts 设计

角度工具。
"""
import math


def degrees_to_radians(degrees: float) -> float:
    """度转弧度"""
    return degrees * math.pi / 180


def radians_to_degrees(radians: float) -> float:
    """弧度转度"""
    return radians * 180 / math.pi


def normalize_angle(angle: float, degrees: bool = True) -> float:
    """
    标准化角度到[0, 360)或[0, 2π)
    
    Args:
        angle: 角度
        degrees: 是否为度
        
    Returns:
        标准化后的角度
    """
    if degrees:
        full = 360
    else:
        full = 2 * math.pi
    
    angle = angle % full
    if angle < 0:
        angle += full
    return angle


def angle_difference(a: float, b: float, degrees: bool = True) -> float:
    """
    两角度间最小差值
    
    Args:
        a: 角度1
        b: 角度2
        degrees: 是否为度
        
    Returns:
        最小差值
    """
    if degrees:
        full = 360
    else:
        full = 2 * math.pi
    
    diff = (b - a) % full
    if diff > full / 2:
        diff -= full
    return diff


def angle_average(*angles: float) -> float:
    """角度平均值（正确处理环绕）"""
    if not angles:
        return 0
    
    x = sum(math.sin(math.radians(a)) for a in angles) / len(angles)
    y = sum(math.cos(math.radians(a)) for a in angles) / len(angles)
    return math.degrees(math.atan2(x, y)) % 360


def rotate_point(x: float, y: float, angle: float, cx: float = 0, cy: float = 0) -> tuple:
    """
    旋转点
    
    Args:
        x, y: 点坐标
        angle: 旋转角度（度）
        cx, cy: 中心点
        
    Returns:
        (新x, 新y)
    """
    rad = math.radians(angle)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    
    dx = x - cx
    dy = y - cy
    
    return (
        cx + dx * cos_a - dy * sin_a,
        cy + dx * sin_a + dy * cos_a
    )


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    计算航向角（两点间）
    
    Args:
        lat1, lon1: 起点
        lat2, lon2: 终点
        
    Returns:
        航向角（度）
    """
    d_lon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    
    x = math.sin(d_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(d_lon)
    
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    计算两点间距离（ Haversine公式）
    
    Args:
        lat1, lon1: 起点
        lat2, lon2: 终点
        
    Returns:
        距离（度为单位，结果需乘以地球半径）
    """
    R = 6371  # 地球半径（公里）
    
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(d_lat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(d_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


class Angle:
    """
    角度对象
    """
    
    def __init__(self, value: float, degrees: bool = True):
        """
        Args:
            value: 角度值
            degrees: 是否为度
        """
        if degrees:
            self._radians = degrees_to_radians(value)
        else:
            self._radians = value
    
    @property
    def degrees(self) -> float:
        return radians_to_degrees(self._radians)
    
    @property
    def radians(self) -> float:
        return self._radians
    
    def __add__(self, other: "Angle") -> "Angle":
        return Angle(self.radians + other.radians, degrees=False)
    
    def __sub__(self, other: "Angle") -> "Angle":
        return Angle(self.radians - other.radians, degrees=False)
    
    def __repr__(self) -> str:
        return f"{self.degrees:.2f}°"


# 导出
__all__ = [
    "degrees_to_radians",
    "radians_to_degrees",
    "normalize_angle",
    "angle_difference",
    "angle_average",
    "rotate_point",
    "bearing",
    "distance",
    "Angle",
]
