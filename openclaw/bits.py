"""
Bits - 位操作
基于 Claude Code bits.ts 设计

位操作工具。
"""


def get_bit(n: int, bit: int) -> int:
    """
    获取指定位
    
    Args:
        n: 数字
        bit: 位索引
        
    Returns:
        0或1
    """
    return (n >> bit) & 1


def set_bit(n: int, bit: int) -> int:
    """
    设置指定位为1
    
    Args:
        n: 数字
        bit: 位索引
        
    Returns:
        新的数字
    """
    return n | (1 << bit)


def clear_bit(n: int, bit: int) -> int:
    """
    清除指定位
    
    Args:
        n: 数字
        bit: 位索引
        
    Returns:
        新的数字
    """
    return n & ~(1 << bit)


def toggle_bit(n: int, bit: int) -> int:
    """
    翻转指定位
    
    Args:
        n: 数字
        bit: 位索引
        
    Returns:
        新的数字
    """
    return n ^ (1 << bit)


def update_bit(n: int, bit: int, value: int) -> int:
    """
    更新指定位
    
    Args:
        n: 数字
        bit: 位索引
        value: 新值(0或1)
        
    Returns:
        新的数字
    """
    return (n & ~(1 << bit)) | ((value & 1) << bit)


def count_ones(n: int) -> int:
    """
    统计1的个数
    
    Args:
        n: 数字
        
    Returns:
        1的个数
    """
    return bin(n).count('1')


def count_zeros(n: int) -> int:
    """
    统计0的个数
    
    Args:
        n: 数字
        
    Returns:
        0的个数
    """
    return n.bit_length() - count_ones(n)


def parity(n: int) -> int:
    """
    奇偶校验位
    
    Args:
        n: 数字
        
    Returns:
        1的个数的奇偶
    """
    return count_ones(n) % 2


def reverse_bits(n: int, width: int = 32) -> int:
    """
    位反转
    
    Args:
        n: 数字
        width: 位宽
        
    Returns:
        反转后的数字
    """
    result = 0
    for i in range(width):
        if n & (1 << i):
            result |= 1 << (width - 1 - i)
    return result


def next_power_of_two(n: int) -> int:
    """
    下一个2的幂
    
    Args:
        n: 数字
        
    Returns:
        下一个2的幂
    """
    if n <= 0:
        return 1
    
    n -= 1
    n |= n >> 1
    n |= n >> 2
    n |= n >> 4
    n |= n >> 8
    n |= n >> 16
    return n + 1


def is_power_of_two(n: int) -> bool:
    """
    是否为2的幂
    
    Args:
        n: 数字
        
    Returns:
        是否为2的幂
    """
    return n > 0 and (n & (n - 1)) == 0


def bit_length(n: int) -> int:
    """
    位长度
    
    Args:
        n: 数字
        
    Returns:
        位长度
    """
    return n.bit_length()


# 导出
__all__ = [
    "get_bit",
    "set_bit",
    "clear_bit",
    "toggle_bit",
    "update_bit",
    "count_ones",
    "count_zeros",
    "parity",
    "reverse_bits",
    "next_power_of_two",
    "is_power_of_two",
    "bit_length",
]
