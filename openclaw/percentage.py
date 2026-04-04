"""
Percentage - 百分比
基于 Claude Code percentage.ts 设计

百分比工具。
"""
from decimal import Decimal, ROUND_HALF_UP


def to_percent(value: float, decimals: int = 2) -> str:
    """
    转为百分比字符串
    
    Args:
        value: 值（0-1之间）
        decimals: 小数位数
        
    Returns:
        百分比字符串
    """
    percent = value * 100
    return f"{percent:.{decimals}f}%"


def from_percent(value: str) -> float:
    """
    从百分比字符串转浮点数
    
    Args:
        value: "50%" -> 0.5
        
    Returns:
        浮点数
    """
    return float(value.rstrip('%')) / 100


def calculate_percent(part: float, whole: float, decimals: int = 2) -> float:
    """
    计算百分比
    
    Args:
        part: 部分
        whole: 总数
        decimals: 小数位数
        
    Returns:
        百分比（0-100）
    """
    if whole == 0:
        return 0.0
    return round(part / whole * 100, decimals)


def calculate_rate(part: float, whole: float, decimals: int = 2) -> float:
    """
    计算比率
    
    Args:
        part: 部分
        whole: 总数
        decimals: 小数位数
        
    Returns:
        比率（0-1）
    """
    if whole == 0:
        return 0.0
    return round(part / whole, decimals)


def percent_of(value: float, percent: float) -> float:
    """
    百分比的绝对值
    
    Args:
        value: 基础值
        percent: 百分比（50 = 50%）
        
    Returns:
        绝对值
    """
    return value * percent / 100


def increase_percent(old_value: float, new_value: float, decimals: int = 2) -> float:
    """
    增长百分比
    
    Args:
        old_value: 旧值
        new_value: 新值
        decimals: 小数位数
        
    Returns:
        增长百分比
    """
    if old_value == 0:
        return 0.0
    return round((new_value - old_value) / old_value * 100, decimals)


def decrease_percent(old_value: float, new_value: float, decimals: int = 2) -> float:
    """
    减少百分比
    
    Args:
        old_value: 旧值
        new_value: 新值
        decimals: 小数位数
        
    Returns:
        减少百分比
    """
    if old_value == 0:
        return 0.0
    return round((old_value - new_value) / old_value * 100, decimals)


def apply_percent(value: float, percent: float) -> float:
    """
    应用百分比变化
    
    Args:
        value: 基础值
        percent: 百分比变化（+10 = 增加10%）
        
    Returns:
        变化后的值
    """
    return value * (1 + percent / 100)


class Percentage:
    """
    百分比对象
    """
    
    def __init__(self, value: float):
        """
        Args:
            value: 0-100之间的值
        """
        self._value = value
    
    @staticmethod
    def of(part: float, whole: float) -> "Percentage":
        """从部分和总数创建"""
        return Percentage(calculate_percent(part, whole))
    
    @staticmethod
    def from_rate(rate: float) -> "Percentage":
        """从比率创建（0-1）"""
        return Percentage(rate * 100)
    
    def to_rate(self) -> float:
        """转为比率（0-1）"""
        return self._value / 100
    
    def of_value(self, value: float) -> float:
        """该百分比的值"""
        return value * self._value / 100
    
    def __repr__(self) -> str:
        return f"{self._value}%"


# 导出
__all__ = [
    "to_percent",
    "from_percent",
    "calculate_percent",
    "calculate_rate",
    "percent_of",
    "increase_percent",
    "decrease_percent",
    "apply_percent",
    "Percentage",
]
