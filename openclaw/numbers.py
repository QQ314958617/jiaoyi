"""
Numbers - 数字工具
基于 Claude Code numbers.ts 设计

数学数字工具。
"""
import math
from typing import List


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
    return math.floor(value * multiplier) / multiplier


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
    return math.ceil(value * multiplier) / multiplier


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


def remap(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
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


def sign(value: float) -> int:
    """
    符号
    
    Returns:
        -1, 0, 或 1
    """
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def gcd(a: int, b: int) -> int:
    """
    最大公约数
    
    Args:
        a: 第一个数
        b: 第二个数
        
    Returns:
        GCD
    """
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a: int, b: int) -> int:
    """
    最小公倍数
    
    Args:
        a: 第一个数
        b: 第二个数
        
    Returns:
        LCM
    """
    return abs(a * b) // gcd(a, b)


def factorial(n: int) -> int:
    """
    阶乘
    
    Args:
        n: 非负整数
        
    Returns:
        n!
    """
    if n < 0:
        raise ValueError("Negative factorial")
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


def fibonacci(n: int) -> int:
    """
    斐波那契数
    
    Args:
        n: 索引
        
    Returns:
        斐波那契数
    """
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b


def is_prime(n: int) -> bool:
    """
    是否为质数
    
    Args:
        n: 整数
        
    Returns:
        是否为质数
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def prime_factors(n: int) -> List[int]:
    """
    质因数分解
    
    Args:
        n: 整数
        
    Returns:
        质因数列表
    """
    factors = []
    d = 2
    
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    
    if n > 1:
        factors.append(n)
    
    return factors


# 导出
__all__ = [
    "clamp",
    "round_decimal",
    "floor_decimal",
    "ceil_decimal",
    "lerp",
    "inverse_lerp",
    "remap",
    "sign",
    "gcd",
    "lcm",
    "factorial",
    "fibonacci",
    "is_prime",
    "prime_factors",
]
