"""
Ratio - 分数
基于 Claude Code ratio.ts 设计

分数/有理数工具。
"""
from typing import Tuple


def gcd(a: int, b: int) -> int:
    """最大公约数"""
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a: int, b: int) -> int:
    """最小公倍数"""
    return abs(a * b) // gcd(a, b)


class Ratio:
    """
    分数
    
    表示精确的有理数。
    """
    
    def __init__(self, numerator: int, denominator: int = 1):
        """
        Args:
            numerator: 分子
            denominator: 分母
        """
        if denominator == 0:
            raise ValueError("Denominator cannot be zero")
        
        # 标准化符号
        if denominator < 0:
            numerator = -numerator
            denominator = -denominator
        
        # 约分
        g = gcd(abs(numerator), abs(denominator))
        self._numerator = numerator // g
        self._denominator = denominator // g
    
    @property
    def numerator(self) -> int:
        return self._numerator
    
    @property
    def denominator(self) -> int:
        return self._denominator
    
    def __repr__(self) -> str:
        if self._denominator == 1:
            return str(self._numerator)
        return f"{self._numerator}/{self._denominator}"
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __float__(self) -> float:
        return self._numerator / self._denominator
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Ratio):
            return (self._numerator == other._numerator and 
                    self._denominator == other._denominator)
        if isinstance(other, int):
            return self._denominator == 1 and self._numerator == other
        return float(self) == float(other)
    
    def __add__(self, other: "Ratio") -> "Ratio":
        if isinstance(other, int):
            other = Ratio(other)
        
        den = lcm(self._denominator, other._denominator)
        num = (self._numerator * (den // self._denominator) + 
                other._numerator * (den // other._denominator))
        return Ratio(num, den)
    
    def __sub__(self, other: "Ratio") -> "Ratio":
        if isinstance(other, int):
            other = Ratio(other)
        
        den = lcm(self._denominator, other._denominator)
        num = (self._numerator * (den // self._denominator) - 
                other._numerator * (den // other._denominator))
        return Ratio(num, den)
    
    def __mul__(self, other: "Ratio") -> "Ratio":
        if isinstance(other, int):
            other = Ratio(other)
        
        num = self._numerator * other._numerator
        den = self._denominator * other._denominator
        return Ratio(num, den)
    
    def __truediv__(self, other: "Ratio") -> "Ratio":
        if isinstance(other, int):
            other = Ratio(other)
        
        if other._numerator == 0:
            raise ZeroDivisionError("Division by zero")
        
        num = self._numerator * other._denominator
        den = self._denominator * other._numerator
        return Ratio(num, den)
    
    def __neg__(self) -> "Ratio":
        return Ratio(-self._numerator, self._denominator)
    
    def __abs__(self) -> "Ratio":
        return Ratio(abs(self._numerator), self._denominator)
    
    def to_float(self) -> float:
        """转为浮点数"""
        return float(self)


# 导出
__all__ = [
    "Ratio",
    "gcd",
    "lcm",
]
