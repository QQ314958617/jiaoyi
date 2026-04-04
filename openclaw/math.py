"""
Math - 数学
基于 Claude Code math.ts 设计

数学工具。
"""
import math


def abs_(x: float) -> float:
    """绝对值"""
    return abs(x)


def ceil(x: float) -> int:
    """向上取整"""
    return math.ceil(x)


def floor(x: float) -> int:
    """向下取整"""
    return math.floor(x)


def round_(x: float) -> int:
    """四舍五入"""
    return round(x)


def sqrt(x: float) -> float:
    """平方根"""
    return math.sqrt(x)


def pow_(x: float, y: float) -> float:
    """幂"""
    return math.pow(x, y)


def log(x: float, base: float = math.e) -> float:
    """对数"""
    if base == math.e:
        return math.log(x)
    return math.log(x, base)


def log10(x: float) -> float:
    """常用对数"""
    return math.log10(x)


def exp(x: float) -> float:
    """指数"""
    return math.exp(x)


def sin(x: float) -> float:
    """正弦"""
    return math.sin(x)


def cos(x: float) -> float:
    """余弦"""
    return math.cos(x)


def tan(x: float) -> float:
    """正切"""
    return math.tan(x)


def asin(x: float) -> float:
    """反正弦"""
    return math.asin(x)


def acos(x: float) -> float:
    """反余弦"""
    return math.acos(x)


def atan(x: float) -> float:
    """反正切"""
    return math.atan(x)


def atan2(y: float, x: float) -> float:
    """atan2"""
    return math.atan2(y, x)


def degrees(x: float) -> float:
    """弧度转角度"""
    return math.degrees(x)


def radians(x: float) -> float:
    """角度转弧度"""
    return math.radians(x)


def pi() -> float:
    """π"""
    return math.pi


def e() -> float:
    """e"""
    return math.e


def sum_(items) -> float:
    """求和"""
    return sum(items)


def product(items) -> float:
    """求积"""
    result = 1
    for item in items:
        result *= item
    return result


def average(items) -> float:
    """平均值"""
    return sum(items) / len(items) if items else 0


def min_(items):
    """最小值"""
    return min(items) if items else None


def max_(items):
    """最大值"""
    return max(items) if items else None


# 导出
__all__ = [
    "abs_", "ceil", "floor", "round_",
    "sqrt", "pow_", "log", "log10", "exp",
    "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
    "degrees", "radians",
    "pi", "e",
    "sum_", "product", "average", "min_", "max_",
]
