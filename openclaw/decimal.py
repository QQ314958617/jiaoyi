"""
Decimal - 高精度小数
基于 Claude Code decimal.ts 设计

高精度小数工具。
"""
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN, ROUND_UP


def to_decimal(value: any, precision: int = None) -> Decimal:
    """
    转换为高精度小数
    
    Args:
        value: 值
        precision: 精度
        
    Returns:
        Decimal
    """
    d = Decimal(str(value))
    if precision is not None:
        quantize_str = '0.' + '0' * precision
        d = d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
    return d


def add(a: any, b: any, precision: int = 2) -> Decimal:
    """加法"""
    result = to_decimal(a) + to_decimal(b)
    if precision is not None:
        quantize_str = '0.' + '0' * precision
        return result.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
    return result


def subtract(a: any, b: any, precision: int = 2) -> Decimal:
    """减法"""
    result = to_decimal(a) - to_decimal(b)
    if precision is not None:
        quantize_str = '0.' + '0' * precision
        return result.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
    return result


def multiply(a: any, b: any, precision: int = 2) -> Decimal:
    """乘法"""
    result = to_decimal(a) * to_decimal(b)
    if precision is not None:
        quantize_str = '0.' + '0' * precision
        return result.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
    return result


def divide(a: any, b: any, precision: int = 2) -> Decimal:
    """除法"""
    result = to_decimal(a) / to_decimal(b)
    if precision is not None:
        quantize_str = '0.' + '0' * precision
        return result.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
    return result


def round_decimal(value: any, precision: int = 2) -> Decimal:
    """四舍五入"""
    d = to_decimal(value)
    quantize_str = '0.' + '0' * precision
    return d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)


def floor_decimal(value: any, precision: int = 2) -> Decimal:
    """向下取整"""
    d = to_decimal(value)
    quantize_str = '0.' + '0' * precision
    return d.quantize(Decimal(quantize_str), rounding=ROUND_DOWN)


def ceil_decimal(value: any, precision: int = 2) -> Decimal:
    """向上取整"""
    d = to_decimal(value)
    quantize_str = '0.' + '0' * precision
    return d.quantize(Decimal(quantize_str), rounding=ROUND_UP)


def truncate(value: any, precision: int = 2) -> Decimal:
    """截断"""
    d = to_decimal(value)
    quantize_str = '0.' + '0' * precision
    return d.quantize(Decimal(quantize_str), rounding=ROUND_DOWN)


# 导出
__all__ = [
    "Decimal",
    "to_decimal",
    "add",
    "subtract",
    "multiply",
    "divide",
    "round_decimal",
    "floor_decimal",
    "ceil_decimal",
    "truncate",
]
