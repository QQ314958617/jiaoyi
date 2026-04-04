"""
Complex - 复数
基于 Claude Code complex.ts 设计

复数工具。
"""
import math
from typing import Tuple


class Complex:
    """
    复数
    
    表示 a + bi 形式的数。
    """
    
    def __init__(self, real: float, imag: float = 0):
        """
        Args:
            real: 实部
            imag: 虚部
        """
        self._real = real
        self._imag = imag
    
    @property
    def real(self) -> float:
        return self._real
    
    @property
    def imag(self) -> float:
        return self._imag
    
    @property
    def conjugate(self) -> "Complex":
        """共轭复数"""
        return Complex(self._real, -self._imag)
    
    @property
    def magnitude(self) -> float:
        """模/绝对值"""
        return math.sqrt(self._real ** 2 + self._imag ** 2)
    
    @property
    def phase(self) -> float:
        """相位角"""
        return math.atan2(self._imag, self._real)
    
    def __repr__(self) -> str:
        if self._imag >= 0:
            return f"{self._real}+{self._imag}i"
        return f"{self._real}{self._imag}i"
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Complex):
            return self._real == other._real and self._imag == other._imag
        if isinstance(other, (int, float)):
            return self._imag == 0 and self._real == other
        return False
    
    def __add__(self, other) -> "Complex":
        if isinstance(other, Complex):
            return Complex(self._real + other._real, self._imag + other._imag)
        if isinstance(other, (int, float)):
            return Complex(self._real + other, self._imag)
        return NotImplemented
    
    def __sub__(self, other) -> "Complex":
        if isinstance(other, Complex):
            return Complex(self._real - other._real, self._imag - other._imag)
        if isinstance(other, (int, float)):
            return Complex(self._real - other, self._imag)
        return NotImplemented
    
    def __mul__(self, other) -> "Complex":
        if isinstance(other, Complex):
            real = self._real * other._real - self._imag * other._imag
            imag = self._real * other._imag + self._imag * other._real
            return Complex(real, imag)
        if isinstance(other, (int, float)):
            return Complex(self._real * other, self._imag * other)
        return NotImplemented
    
    def __truediv__(self, other) -> "Complex":
        if isinstance(other, Complex):
            denom = other._real ** 2 + other._imag ** 2
            if denom == 0:
                raise ZeroDivisionError("Division by zero")
            real = (self._real * other._real + self._imag * other._imag) / denom
            imag = (self._imag * other._real - self._real * other._imag) / denom
            return Complex(real, imag)
        if isinstance(other, (int, float)):
            return Complex(self._real / other, self._imag / other)
        return NotImplemented
    
    def __neg__(self) -> "Complex":
        return Complex(-self._real, -self._imag)
    
    def __abs__(self) -> float:
        return self.magnitude
    
    def to_tuple(self) -> Tuple[float, float]:
        """转为(实部, 虚部)元组"""
        return (self._real, self._imag)
    
    @staticmethod
    def from_polar(r: float, theta: float) -> "Complex":
        """从极坐标创建"""
        return Complex(r * math.cos(theta), r * math.sin(theta))


# 导出
__all__ = [
    "Complex",
]
