"""
Sampler - 采样器
基于 Claude Code sampler.ts 设计

随机采样工具。
"""
import random
from typing import Callable, List, TypeVar

T = TypeVar('T')


def sample(items: List[T], k: int) -> List[T]:
    """
    随机采样k个元素
    
    Args:
        items: 列表
        k: 采样数量
        
    Returns:
        采样结果
    """
    if k >= len(items):
        return list(items)
    return random.sample(items, k)


def weighted_sample(
    items: List[T],
    weights: List[float],
    k: int,
) -> List[T]:
    """
    加权随机采样
    
    Args:
        items: 列表
        weights: 权重列表
        k: 采样数量
        
    Returns:
        采样结果
    """
    if k >= len(items):
        return list(items)
    
    return random.choices(
        population=items,
        weights=weights,
        k=k,
    )


def reservoir_sample(items: List[T], k: int) -> List[T]:
    """
    水库采样
    
    用于从超大数据流中均匀采样k个元素。
    时间复杂度O(n)，空间复杂度O(k)。
    
    Args:
        items: 数据流
        k: 采样数量
        
    Returns:
        采样结果
    """
    if k >= len(items):
        return list(items)
    
    result = items[:k]
    
    for i in range(k, len(items)):
        j = random.randint(0, i)
        if j < k:
            result[j] = items[i]
    
    return result


def shuffle(items: List[T]) -> List[T]:
    """
    随机洗牌
    
    Args:
        items: 列表
        
    Returns:
        洗牌后的新列表
    """
    result = list(items)
    random.shuffle(result)
    return result


def random_bool(probability: float = 0.5) -> bool:
    """
    随机布尔值
    
    Args:
        probability: True的概率
        
    Returns:
        随机布尔值
    """
    return random.random() < probability


def random_int(min_val: int, max_val: int) -> int:
    """
    随机整数
    
    Args:
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        随机整数
    """
    return random.randint(min_val, max_val)


def random_float(min_val: float, max_val: float) -> float:
    """
    随机浮点数
    
    Args:
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        随机浮点数
    """
    return random.uniform(min_val, max_val)


def random_choice(items: List[T]) -> T:
    """
    随机选择
    
    Args:
        items: 列表
        
    Returns:
        随机选择的元素
    """
    if not items:
        raise ValueError("Cannot choose from empty list")
    return random.choice(items)


def random_string(length: int, charset: str = None) -> str:
    """
    随机字符串
    
    Args:
        length: 长度
        charset: 字符集（默认字母数字）
        
    Returns:
        随机字符串
    """
    if charset is None:
        charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    
    return ''.join(random.choice(charset) for _ in range(length))


class Sampler:
    """
    采样器
    
    提供可配置的采样功能。
    """
    
    def __init__(self, seed: int = None):
        """
        Args:
            seed: 随机种子
        """
        if seed is not None:
            random.seed(seed)
    
    def sample(self, items: List[T], k: int) -> List[T]:
        """随机采样"""
        return sample(items, k)
    
    def weighted_sample(
        self,
        items: List[T],
        weights: List[float],
        k: int,
    ) -> List[T]:
        """加权采样"""
        return weighted_sample(items, weights, k)
    
    def reservoir_sample(self, items: List[T], k: int) -> List[T]:
        """水库采样"""
        return reservoir_sample(items, k)
    
    def shuffle(self, items: List[T]) -> List[T]:
        """洗牌"""
        return shuffle(items)
    
    def choice(self, items: List[T]) -> T:
        """随机选择"""
        return random_choice(items)


# 导出
__all__ = [
    "sample",
    "weighted_sample",
    "reservoir_sample",
    "shuffle",
    "random_bool",
    "random_int",
    "random_float",
    "random_choice",
    "random_string",
    "Sampler",
]
