"""
BloomFilter - 布隆过滤器
基于 Claude Code bloomFilter.ts 设计

空间效率高的概率性集合。
"""
import hashlib
from typing import Generic, TypeVar

T = TypeVar('T')


class BloomFilter(Generic[T]):
    """
    布隆过滤器
    
    空间高效的概率性数据结构。
    可能产生假阳性，但不会产生假阴性。
    """
    
    def __init__(self, size: int = 1000, hash_count: int = 7):
        """
        Args:
            size: 位数组大小
            hash_count: 哈希函数数量
        """
        self._size = size
        self._hash_count = hash_count
        self._bits = [False] * size
    
    def _hash_values(self, item: str) -> list:
        """计算多个哈希值"""
        result = []
        
        for i in range(self._hash_count):
            data = f"{item}:{i}".encode()
            hash_val = int(hashlib.md5(data).hexdigest(), 16)
            result.append(hash_val % self._size)
        
        return result
    
    def add(self, item: str) -> None:
        """添加元素"""
        for idx in self._hash_values(item):
            self._bits[idx] = True
    
    def contains(self, item: str) -> bool:
        """检查元素是否可能存在"""
        return all(self._bits[idx] for idx in self._hash_values(item))
    
    def __contains__(self, item: str) -> bool:
        return self.contains(item)
    
    def reset(self) -> None:
        """重置过滤器"""
        self._bits = [False] * self._size
    
    @property
    def size(self) -> int:
        """位数组大小"""
        return self._size
    
    @property
    def hash_count(self) -> int:
        """哈希函数数量"""
        return self._hash_count


class ScalableBloomFilter:
    """
    可扩展布隆过滤器
    
    当过滤器满时自动扩展。
    """
    
    def __init__(
        self,
        initial_size: int = 1000,
        hash_count: int = 7,
        scale_factor: float = 2.0,
    ):
        """
        Args:
            initial_size: 初始大小
            hash_count: 哈希函数数量
            scale_factor: 扩展倍数
        """
        self._initial_size = initial_size
        self._hash_count = hash_count
        self._scale_factor = scale_factor
        self._filters: list[BloomFilter] = [
            BloomFilter(initial_size, hash_count)
        ]
    
    def add(self, item: str) -> None:
        """添加元素"""
        current = self._filters[-1]
        
        if current.size >= current.size * 0.7:
            new_size = int(current.size * self._scale_factor)
            self._filters.append(
                BloomFilter(new_size, self._hash_count)
            )
        
        self._filters[-1].add(item)
    
    def contains(self, item: str) -> bool:
        """检查元素"""
        return any(f.contains(item) for f in self._filters)
    
    def __contains__(self, item: str) -> bool:
        return self.contains(item)


# 导出
__all__ = [
    "BloomFilter",
    "ScalableBloomFilter",
]
