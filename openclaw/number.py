"""
Number - 数字工具
基于 Claude Code number.ts 设计

数字处理工具。
"""
from typing import Optional


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    限制范围
    
    Args:
        value: 值
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        限制后的值
    """
    return max(min_val, min(max_val, value))


def round_decimal(value: float, decimals: int = 2) -> float:
    """
    四舍五入
    
    Args:
        value: 值
        decimals: 小数位数
        
    Returns:
        舍入后的值
    """
    multiplier = 10 ** decimals
    return round(value * multiplier) / multiplier


def floor_decimal(value: float, decimals: int = 2) -> float:
    """
    向下取整
    
    Args:
        value: 值
        decimals: 小数位数
        
    Returns:
        向下取整后的值
    """
    multiplier = 10 ** decimals
    return int(value * multiplier) / multiplier


def ceil_decimal(value: float, decimals: int = 2) -> float:
    """
    向上取整
    
    Args:
        value: 值
        decimals: 小数位数
        
    Returns:
        向上取整后的值
    """
    multiplier = 10 ** decimals
    import math
    return math.ceil(value * multiplier) / multiplier


def format_number(value: float, decimals: int = 0) -> str:
    """
    格式化数字
    
    Args:
        value: 值
        decimals: 小数位数
        
    Returns:
        格式化字符串
    """
    return f"{value:,.{decimals}f}"


def format_currency(
    value: float,
    symbol: str = '¥',
    decimals: int = 2,
) -> str:
    """
    格式化货币
    
    Args:
        value: 值
        symbol: 货币符号
        decimals: 小数位数
        
    Returns:
        货币字符串
    """
    return f"{symbol}{value:,.{decimals}f}"


def format_percent(value: float, decimals: int = 1) -> str:
    """
    格式化百分比
    
    Args:
        value: 值 (0-1 或 0-100)
        decimals: 小数位数
        
    Returns:
        百分比字符串
    """
    if value <= 1:
        value *= 100
    return f"{value:.{decimals}f}%"


def parse_number(text: str) -> Optional[float]:
    """
    解析数字
    
    Args:
        text: 字符串
        
    Returns:
        数字或None
    """
    try:
        return float(text.replace(',', ''))
    except (ValueError, AttributeError):
        return None


def is_even(value: int) -> bool:
    """是否为偶数"""
    return value % 2 == 0


def is_odd(value: int) -> bool:
    """是否为奇数"""
    return value % 2 != 0


def is_positive(value: float) -> bool:
    """是否为正数"""
    return value > 0


def is_negative(value: float) -> bool:
    """是否为负数"""
    return value < 0


def is_zero(value: float) -> bool:
    """是否为零"""
    return value == 0


def abs(value: float) -> float:
    """绝对值"""
    return abs(value) if value >= 0 else -value


def sign(value: float) -> int:
    """符号 (-1, 0, 1)"""
    if value > 0: return 1
    if value < 0: return -1
    return 0


def in_range(value: float, min_val: float, max_val: float) -> bool:
    """是否在范围内"""
    return min_val <= value <= max_val


def random_int(min_val: int, max_val: int) -> int:
    """随机整数"""
    import random
    return random.randint(min_val, max_val)


# 数字缩放
def kilo(value: float) -> float:
    """转千"""
    return value / 1000


def mega(value: float) -> float:
    """转百万"""
    return value / 1000000


def giga(value: float) -> float:
    """转十亿"""
    return value / 1000000000


# 字节缩放
def bytes_to_kb(bytes_val: float) -> float:
    """字节转KB"""
    return bytes_val / 1024


def bytes_to_mb(bytes_val: float) -> float:
    """字节转MB"""
    return bytes_val / (1024 * 1024)


def bytes_to_gb(bytes_val: float) -> float:
    """字节转GB"""
    return bytes_val / (1024 * 1024 * 1024)


# 导出
__all__ = [
    "clamp",
    "round_decimal",
    "floor_decimal",
    "ceil_decimal",
    "format_number",
    "format_currency",
    "format_percent",
    "parse_number",
    "is_even",
    "is_odd",
    "is_positive",
    "is_negative",
    "is_zero",
    "sign",
    "in_range",
    "random_int",
    "kilo",
    "mega",
    "giga",
    "bytes_to_kb",
    "bytes_to_mb",
    "bytes_to_gb",
]
