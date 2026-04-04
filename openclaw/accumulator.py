"""
Accumulator - 累加器
基于 Claude Code accumulator.ts 设计

累加工具。
"""
from typing import Any, Callable, List, TypeVar

T = TypeVar('T')


class Accumulator:
    """
    累加器
    
    收集值并应用操作。
    """
    
    def __init__(self, initial: T = None, combine: Callable[[T, T], T] = None):
        """
        Args:
            initial: 初始值
            combine: 合并函数 (acc, item) -> new_acc
        """
        self._value = initial
        self._combine = combine
    
    def add(self, value: T) -> "Accumulator":
        """添加值"""
        if self._value is None:
            self._value = value
        elif self._combine:
            self._value = self._combine(self._value, value)
        return self
    
    def get(self) -> T:
        """获取当前值"""
        return self._value
    
    def reset(self, initial: T = None) -> None:
        """重置"""
        self._value = initial
    
    @property
    def value(self) -> T:
        return self.get()


def sum_numbers(numbers: List[float]) -> float:
    """
    求和
    
    Args:
        numbers: 数字列表
        
    Returns:
        总和
    """
    return sum(numbers)


def product_numbers(numbers: List[float]) -> float:
    """
    求积
    
    Args:
        numbers: 数字列表
        
    Returns:
        乘积
    """
    result = 1
    for n in numbers:
        result *= n
    return result


def count(items: List[Any]) -> int:
    """
    计数
    
    Args:
        items: 列表
        
    Returns:
        数量
    """
    return len(items)


def average(numbers: List[float]) -> float:
    """
    平均值
    
    Args:
        numbers: 数字列表
        
    Returns:
        平均值
    """
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


def aggregate(
    items: List[T],
    aggregators: dict,
) -> dict:
    """
    聚合操作
    
    Args:
        items: 项目列表
        aggregators: {名称: 聚合函数}
        
    Returns:
        聚合结果
    """
    result = {}
    
    for name, fn in aggregators.items():
        try:
            result[name] = fn(items)
        except Exception:
            result[name] = None
    
    return result


def group_aggregate(
    items: List[dict],
    group_key: str,
    aggregators: dict,
) -> dict:
    """
    分组聚合
    
    Args:
        items: 项目列表
        group_key: 分组键
        aggregators: {名称: 聚合函数}
        
    Returns:
        {组名: {聚合名: 值}}
    """
    groups: dict = {}
    
    for item in items:
        if isinstance(item, dict):
            key = item.get(group_key)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
    
    result = {}
    for key, group_items in groups.items():
        result[key] = aggregate(group_items, aggregators)
    
    return result


class StatCounter:
    """
    统计计数器
    
    计算基本统计信息。
    """
    
    def __init__(self):
        self._count = 0
        self._sum = 0.0
        self._min = None
        self._max = None
        self._values: List[float] = []
    
    def add(self, value: float) -> None:
        """添加值"""
        self._count += 1
        self._sum += value
        self._values.append(value)
        
        if self._min is None or value < self._min:
            self._min = value
        if self._max is None or value > self._max:
            self._max = value
    
    @property
    def count(self) -> int:
        return self._count
    
    @property
    def sum(self) -> float:
        return self._sum
    
    @property
    def mean(self) -> float:
        return self._sum / self._count if self._count > 0 else 0
    
    @property
    def min(self) -> float:
        return self._min
    
    @property
    def max(self) -> float:
        return self._max
    
    @property
    def variance(self) -> float:
        if self._count < 2:
            return 0
        mean = self.mean
        return sum((x - mean) ** 2 for x in self._values) / self._count
    
    @property
    def stddev(self) -> float:
        import math
        return math.sqrt(self.variance)


# 导出
__all__ = [
    "Accumulator",
    "sum_numbers",
    "product_numbers",
    "count",
    "average",
    "aggregate",
    "group_aggregate",
    "StatCounter",
]
