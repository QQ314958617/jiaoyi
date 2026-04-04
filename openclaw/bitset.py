"""
BitSet - 位集
基于 Claude Code bitset.ts 设计

位集工具。
"""
from typing import List


class BitSet:
    """
    位集
    
    用位存储布尔值集合。
    """
    
    def __init__(self, size: int):
        """
        Args:
            size: 位数量
        """
        self._size = size
        self._words = [0] * ((size + 63) // 64)  # 每64位一个word
    
    def _word_index(self, bit: int) -> int:
        """获取位所在的word索引"""
        return bit // 64
    
    def _bit_index(self, bit: int) -> int:
        """获取位在word内的索引"""
        return bit % 64
    
    def set(self, bit: int, value: bool = True) -> None:
        """
        设置位
        
        Args:
            bit: 位索引
            value: 要设置的值
        """
        if bit < 0 or bit >= self._size:
            raise IndexError(f"Bit index {bit} out of range")
        
        word_idx = self._word_index(bit)
        bit_idx = self._bit_index(bit)
        
        if value:
            self._words[word_idx] |= (1 << bit_idx)
        else:
            self._words[word_idx] &= ~(1 << bit_idx)
    
    def get(self, bit: int) -> bool:
        """
        获取位
        
        Args:
            bit: 位索引
            
        Returns:
            位值
        """
        if bit < 0 or bit >= self._size:
            raise IndexError(f"Bit index {bit} out of range")
        
        word_idx = self._word_index(bit)
        bit_idx = self._bit_index(bit)
        
        return bool(self._words[word_idx] & (1 << bit_idx))
    
    def __setitem__(self, bit: int, value: bool) -> None:
        self.set(bit, value)
    
    def __getitem__(self, bit: int) -> bool:
        return self.get(bit)
    
    def clear(self) -> None:
        """清空所有位"""
        for i in range(len(self._words)):
            self._words[i] = 0
    
    def set_all(self) -> None:
        """设置所有位"""
        for i in range(len(self._words)):
            self._words[i] = (1 << 64) - 1
        
        # 清除超出范围的位
        excess = self._size % 64
        if excess != 0:
            self._words[-1] &= (1 << excess) - 1
    
    def count(self) -> int:
        """设置位数"""
        total = 0
        for word in self._words:
            while word:
                total += 1
                word &= word - 1  # 清除最低位的1
        return total
    
    def any(self) -> bool:
        """是否有任意位设置"""
        return any(word != 0 for word in self._words)
    
    def none(self) -> bool:
        """是否没有位设置"""
        return not self.any()
    
    def all(self) -> bool:
        """是否所有位都设置"""
        # 检查完整的words
        for i in range(len(self._words) - 1):
            if self._words[i] != (1 << 64) - 1:
                return False
        
        # 检查最后一个word
        excess = self._size % 64
        if excess == 0:
            return self._words[-1] == (1 << 64) - 1
        else:
            mask = (1 << excess) - 1
            return self._words[-1] == mask
    
    def union(self, other: "BitSet") -> "BitSet":
        """
        并集
        
        Args:
            other: 另一个BitSet
            
        Returns:
            新的BitSet
        """
        if self._size != other._size:
            raise ValueError("BitSets must have the same size")
        
        result = BitSet(self._size)
        for i in range(len(self._words)):
            result._words[i] = self._words[i] | other._words[i]
        return result
    
    def intersection(self, other: "BitSet") -> "BitSet":
        """
        交集
        
        Args:
            other: 另一个BitSet
            
        Returns:
            新的BitSet
        """
        if self._size != other._size:
            raise ValueError("BitSets must have the same size")
        
        result = BitSet(self._size)
        for i in range(len(self._words)):
            result._words[i] = self._words[i] & other._words[i]
        return result
    
    @property
    def size(self) -> int:
        return self._size


# 导出
__all__ = [
    "BitSet",
]
