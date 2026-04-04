"""
SkipList - 跳表
基于 Claude Code skipList.ts 设计

O(log n)查找的有序链表。
"""
import random
from typing import Generic, Optional, TypeVar

T = TypeVar('T')


class SkipListNode(Generic[T]):
    """跳表节点"""
    
    def __init__(self, value: T, level: int):
        self.value = value
        self.level = level
        self.forward: list = [None] * (level + 1)


class SkipList(Generic[T]):
    """
    跳表
    
    平均O(log n)查找、插入、删除的有序数据结构。
    """
    
    def __init__(self, max_level: int = 16, p: float = 0.5):
        """
        Args:
            max_level: 最大层数
            p: 概率参数
        """
        self._max_level = max_level
        self._p = p
        self._header = SkipListNode(None, max_level)
        self._level = 0
        self._size = 0
    
    def _random_level(self) -> int:
        """随机层数"""
        level = 0
        while random.random() < self._p and level < self._max_level:
            level += 1
        return level
    
    def insert(self, value: T) -> None:
        """插入值"""
        update = [None] * (self._max_level + 1)
        current = self._header
        
        # 查找插入位置
        for i in range(self._level, -1, -1):
            while current.forward[i] and current.forward[i].value < value:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        # 已存在
        if current and current.value == value:
            return
        
        # 随机层数
        new_level = self._random_level()
        
        # 更新层数
        if new_level > self._level:
            for i in range(self._level + 1, new_level + 1):
                update[i] = self._header
            self._level = new_level
        
        # 创建新节点
        node = SkipListNode(value, new_level)
        
        # 插入
        for i in range(new_level + 1):
            node.forward[i] = update[i].forward[i]
            update[i].forward[i] = node
        
        self._size += 1
    
    def search(self, value: T) -> Optional[T]:
        """搜索值"""
        current = self._header
        
        for i in range(self._level, -1, -1):
            while current.forward[i] and current.forward[i].value < value:
                current = current.forward[i]
        
        current = current.forward[0]
        
        if current and current.value == value:
            return current.value
        
        return None
    
    def remove(self, value: T) -> bool:
        """删除值"""
        update = [None] * (self._max_level + 1)
        current = self._header
        
        for i in range(self._level, -1, -1):
            while current.forward[i] and current.forward[i].value < value:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if not current or current.value != value:
            return False
        
        # 删除
        for i in range(current.level + 1):
            if update[i].forward[i] != current:
                break
            update[i].forward[i] = current.forward[i]
        
        # 降低层数
        while self._level > 0 and self._header.forward[self._level] is None:
            self._level -= 1
        
        self._size -= 1
        return True
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, value: T) -> bool:
        return self.search(value) is not None
    
    def traverse(self):
        """遍历所有值"""
        current = self._header.forward[0]
        while current:
            yield current.value
            current = current.forward[0]


# 导出
__all__ = [
    "SkipList",
    "SkipListNode",
]
