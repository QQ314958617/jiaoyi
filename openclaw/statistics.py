"""
Statistics - 统计
基于 Claude Code stats.ts 设计

统计工具。
"""
import math
from typing import List


def mean(values: List[float]) -> float:
    """平均值"""
    if not values:
        return 0
    return sum(values) / len(values)


def median(values: List[float]) -> float:
    """中位数"""
    if not values:
        return 0
    
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    
    if n % 2 == 0:
        return (sorted_vals[n//2-1] + sorted_vals[n//2]) / 2
    return sorted_vals[n//2]


def mode(values: List) -> any:
    """众数"""
    if not values:
        return None
    
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    
    max_count = max(counts.values())
    
    for v, c in counts.items():
        if c == max_count:
            return v


def variance(values: List[float]) -> float:
    """方差"""
    if not values:
        return 0
    
    avg = mean(values)
    return mean([(x - avg) ** 2 for x in values])


def stdev(values: List[float]) -> float:
    """标准差"""
    return math.sqrt(variance(values))


def percentile(values: List[float], p: float) -> float:
    """
    百分位数
    
    Args:
        values: 值列表
        p: 百分位（0-100）
        
    Returns:
        百分位数
    """
    if not values:
        return 0
    
    sorted_vals = sorted(values)
    index = (len(sorted_vals) - 1) * p / 100
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    
    if lower == upper:
        return sorted_vals[lower]
    
    weight = index - lower
    return sorted_vals[lower] * (1 - weight) + sorted_vals[upper] * weight


def quartile(values: List[float]) -> tuple:
    """四分位数"""
    return (percentile(values, 25), percentile(values, 50), percentile(values, 75))


def skewness(values: List[float]) -> float:
    """偏度"""
    if not values:
        return 0
    
    avg = mean(values)
    s = stdev(values)
    
    if s == 0:
        return 0
    
    n = len(values)
    return (n / ((n-1) * (n-2))) * sum(((x - avg) / s) ** 3 for x in values)


def kurtosis(values: List[float]) -> float:
    """峰度"""
    if not values:
        return 0
    
    avg = mean(values)
    s = stdev(values)
    
    if s == 0:
        return 0
    
    n = len(values)
    return (n * (n+1) / ((n-1) * (n-2) * (n-3))) * sum(((x - avg) / s) ** 4 for x in values) - 3 * (n-1)**2 / ((n-2) * (n-3))


def covariance(x: List[float], y: List[float]) -> float:
    """协方差"""
    if len(x) != len(y) or not x:
        return 0
    
    mean_x = mean(x)
    mean_y = mean(y)
    
    return mean([(xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)])


def correlation(x: List[float], y: List[float]) -> float:
    """相关系数"""
    if not x or len(x) != len(y):
        return 0
    
    cov = covariance(x, y)
    sx = stdev(x)
    sy = stdev(y)
    
    if sx == 0 or sy == 0:
        return 0
    
    return cov / (sx * sy)


# 导出
__all__ = [
    "mean",
    "median",
    "mode",
    "variance",
    "stdev",
    "percentile",
    "quartile",
    "skewness",
    "kurtosis",
    "covariance",
    "correlation",
]
