"""
Random - 随机工具
基于 Claude Code random.ts 设计

随机数生成工具。
"""
import random
import string
import uuid
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
        probability: True的概率
        
    Returns:
        随机布尔值
    """
    return random.random() < probability


def random_choice(seq: Sequence) -> any:
    """
    随机选择
    
    Args:
        seq: 序列
        
    Returns:
        随机元素
    """
    return random.choice(seq)


def random_choices(seq: Sequence, k: int) -> List:
    """
    随机选择多个
    
    Args:
        seq: 序列
        k: 选择数量
        
    Returns:
        随机元素列表
    """
    return random.choices(seq, k=k)


def random_sample(seq: Sequence, k: int) -> List:
    """
    随机抽样（不重复）
    
    Args:
        seq: 序列
        k: 抽样数量
        
    Returns:
        抽样列表
    """
    return random.sample(seq, k=k)


def random_string(length: int = 10, charset: str = None) -> str:
    """
    随机字符串
    
    Args:
        length: 长度
        charset: 字符集
        
    Returns:
        随机字符串
    """
    if charset is None:
        charset = string.ascii_letters + string.digits
    
    return ''.join(random.choice(charset) for _ in range(length))


def random_alpha(length: int = 10) -> str:
    """随机字母字符串"""
    return random_string(length, string.ascii_letters)


def random_numeric(length: int = 10) -> str:
    """随机数字字符串"""
    return random_string(length, string.digits)


def random_alphanumeric(length: int = 10) -> str:
    """随机字母数字字符串"""
    return random_string(length, string.ascii_letters + string.digits)


def random_uuid() -> str:
    """随机UUID"""
    return str(uuid.uuid4())


def random_hex(length: int = 10) -> str:
    """随机十六进制字符串"""
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))


def shuffle(seq: Sequence) -> List:
    """
    洗牌
    
    Args:
        seq: 序列
        
    Returns:
        洗牌后的列表
    """
    result = list(seq)
    random.shuffle(result)
    return result


def random_color() -> str:
    """随机颜色（十六进制）"""
    return '#{:06x}'.format(random.randint(0, 0xffffff))


def random_date(days_back: int = 365) -> str:
    """随机日期（ISO格式）"""
    import datetime
    days = random.randint(0, days_back)
    return (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()


# 带权重的随机选择
def weighted_choice(choices: List[tuple], k: int = 1) -> any:
    """
    权重随机选择
    
    Args:
        choices: [(选项, 权重), ...]
        k: 选择数量
        
    Returns:
        随机选择的选项
    """
    options, weights = zip(*choices)
    selected = random.choices(options, weights=weights, k=k)
    return selected if k > 1 else selected[0]


# 导出
__all__ = [
    "random_int",
    "random_float",
    "random_bool",
    "random_choice",
    "random_choices",
    "random_sample",
    "random_string",
    "random_alpha",
    "random_numeric",
    "random_alphanumeric",
    "random_uuid",
    "random_hex",
    "shuffle",
    "random_color",
    "random_date",
    "weighted_choice",
]
