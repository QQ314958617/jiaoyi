"""
BloomFilter - 布隆过滤器
基于 Claude Code bloom.ts 设计

布隆过滤器实现。
"""
import hashlib
from typing import List


class BloomFilter:
    """
    布隆过滤器
    
    空间效率高的概率性集合。
    """
    
    def __init__(self, size: int = 1000, hash_count: int = 3):
        """
        Args:
            size: 位数组大小
            hash_count: 哈希函数数量
        """
        self._size = size
        self._hash_count = hash_count
        self._bits = [False] * size
    
    def _hashes(self, item: str) -> List[int]:
        """
        计算多个哈希值
        
        Args:
            item: 项
            
        Returns:
            哈希值列表
        """
        result = []
        
        for i in range(self._hash_count):
            data = f"{item}:{i}".encode()
            hash_val = int(hashlib.md5(data).hexdigest(), 16)
            result.append(hash_val % self._size)
        
        return result
    
    def add(self, item: str) -> None:
        """
        添加项
        
        Args:
            item: 项
        """
        for idx in self._hashes(item):
            self._bits[idx] = True
    
    def might_contain(self, item: str) -> bool:
        """
        检查项是否可能存在
        
        Args:
            item: 项
            
        Returns:
            可能存在返回True，不存在返回False
        """
        for idx in self._hashes(item):
            if not self._bits[idx]:
                return False
        return True
    
    def __contains__(self, item: str) -> bool:
        return self.might_contain(item)
    
    def clear(self) -> None:
        """清空"""
        for i in range(self._size):
            self._bits[i] = False
    
    @property
    def size(self) -> int:
        return self._size
    
    @property
    def hash_count(self) -> int:
        return self._hash_count
    
    def fill_ratio(self) -> float:
        """
        填充比率
        
        Returns:
            已设置位数 / 总位数
        """
        return sum(self._bits) / self._size


# 导出
__all__ = [
    "BloomFilter",
]
