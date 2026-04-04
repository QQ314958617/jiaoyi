"""
Number - 数字
基于 Claude Code number.ts 设计

数字工具。
"""
import re
from typing import Union


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    限制在范围内
    
    Args:
        value: 值
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        限制后的值
    """
    return max(min_val, min(max_val, value))


def lerp(a: float, b: float, t: float) -> float:
    """
    线性插值
    
    Args:
        a: 起始值
        b: 结束值
        t: 插值因子(0-1)
        
    Returns:
        插值结果
    """
    return a + (b - a) * t


def inverse_lerp(a: float, b: float, value: float) -> float:
    """
    逆向线性插值
    
    Args:
        a: 起始值
        b: 结束值
        value: 当前值
        
    Returns:
        插值因子
    """
    if a == b:
        return 0.0
    return (value - a) / (b - a)


def remap(value: float, in_min: float, in_max: float, 
          out_min: float, out_max: float) -> float:
    """
    重映射
    
    Args:
        value: 值
        in_min, in_max: 输入范围
        out_min, out_max: 输出范围
        
    Returns:
        重映射后的值
    """
    t = inverse_lerp(in_min, in_max, value)
    return lerp(out_min, out_max, t)


def round_to(value: float, precision: int) -> float:
    """
    四舍五入到指定精度
    
    Args:
        value: 值
        precision: 小数位数
        
    Returns:
        舍入后的值
    """
    multiplier = 10 ** precision
    return round(value * multiplier) / multiplier


def floor_to(value: float, precision: int) -> float:
    """
    向下取整到指定精度
    
    Args:
        value: 值
        precision: 小数位数
        
    Returns:
        向下取整后的值
    """
    import math
    multiplier = 10 ** precision
    return math.floor(value * multiplier) / multiplier


def ceil_to(value: float, precision: int) -> float:
    """
    向上取整到指定精度
    
    Args:
        value: 值
        precision: 小数位数
        
    Returns:
        向上取整后的值
    """
    import math
    multiplier = 10 ** precision
    return math.ceil(value * multiplier) / multiplier


def is_even(n: int) -> bool:
    """是否为偶数"""
    return n % 2 == 0


def is_odd(n: int) -> bool:
    """是否为奇数"""
    return n % 2 != 0


def is_between(value: float, min_val: float, max_val: float) -> bool:
    """是否在范围内"""
    return min_val <= value <= max_val


def sign(value: float) -> int:
    """符号"""
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def truncate(value: float, precision: int = 0) -> float:
    """
    截断
    
    Args:
        value: 值
        precision: 小数位数
        
    Returns:
        截断后的值
    """
    multiplier = 10 ** precision
    return int(value * multiplier) / multiplier


# 导出
__all__ = [
    "clamp",
    "lerp",
    "inverse_lerp",
    "remap",
    "round_to",
    "floor_to",
    "ceil_to",
    "is_even",
    "is_odd",
    "is_between",
    "sign",
    "truncate",
]
