"""
Random2 - 随机
基于 Claude Code random.ts 设计

随机工具。
"""
import random
import string
from typing import List, Sequence


def random_int(min_val: int = 0, max_val: int = 100) -> int:
    """
    随机整数
    
    Args:
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        随机整数
    """
    return random.randint(min_val, max_val)


def random_float(min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    随机浮点数
    
    Args:
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        随机浮点数
    """
    return random.uniform(min_val, max_val)


def random_bool(probability: float = 0.5) -> bool:
    """
    随机布尔值
    
    Args:
        probability: True概率
        
    Returns:
        随机布尔值
    """
    return random.random() < probability


def random_choice(choices: Sequence) -> any:
    """
    随机选择
    
    Args:
        choices: 选项序列
        
    Returns:
        随机选项
    """
    return random.choice(choices)


def random_sample(population: Sequence, k: int) -> List:
    """
    随机抽样（不重复）
    
    Args:
        population: 总体
        k: 样本数
        
    Returns:
        样本列表
    """
    return random.sample(population, k)


def random_shuffle(items: List) -> List:
    """
    随机打乱
    
    Args:
        items: 列表
        
    Returns:
        打乱后的列表
    """
    result = list(items)
    random.shuffle(result)
    return result


def random_string(length: int = 16, chars: str = None) -> str:
    """
    随机字符串
    
    Args:
        length: 长度
        chars: 字符集
        
    Returns:
        随机字符串
    """
    if chars is None:
        chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def random_hex(length: int = 16) -> str:
    """随机十六进制字符串"""
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))


def random_uuid() -> str:
    """随机UUID"""
    import uuid
    return str(uuid.uuid4())


def random_bytes(length: int = 16) -> bytes:
    """随机字节"""
    return bytes(random.randint(0, 255) for _ in range(length))


def random_color() -> str:
    """随机颜色（十六进制）"""
    return '#{:06x}'.format(random.randint(0, 0xffffff))


# 全局随机实例
_default_random = random.Random()


def seed(value: int) -> None:
    """设置随机种子"""
    random.seed(value)


# 导出
__all__ = [
    "random_int",
    "random_float",
    "random_bool",
    "random_choice",
    "random_sample",
    "random_shuffle",
    "random_string",
    "random_hex",
    "random_uuid",
    "random_bytes",
    "random_color",
    "seed",
]
