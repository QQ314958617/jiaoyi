"""
SkipList - 跳表
基于 Claude Code skiplist.ts 设计

跳表实现。
"""
import random
from typing import Any, Callable, List, Optional


class SkipListNode:
    """跳表节点"""
    
    def __init__(self, value: Any, level: int = 0):
        self.value = value
        self._forward: List[Optional["SkipListNode"]] = [None] * (level + 1)


class SkipList:
    """
    跳表
    
    对数时间复杂度的有序链表。
    """
    
    def __init__(self, max_level: int = 16, probability: float = 0.5):
        """
        Args:
            max_level: 最大层数
            probability: 提升概率
        """
        self._max_level = max_level
        self._probability = probability
        self._header = SkipListNode(None, max_level)
        self._level = 0
        self._size = 0
    
    def _random_level(self) -> int:
        """随机层数"""
        level = 0
        while level < self._max_level and random.random() < self._probability:
            level += 1
        return level
    
    def insert(self, value: Any) -> None:
        """
        插入值
        
        Args:
            value: 值
        """
        update = [None] * (self._max_level + 1)
        current = self._header
        
        # 找到每层的前驱
        for i in range(self._level, -1, -1):
            while current._forward[i] and current._forward[i].value < value:
                current = current._forward[i]
            update[i] = current
        
        current = current._forward[0]
        
        # 如果已存在则更新
        if current and current.value == value:
            current.value = value
            return
        
        # 创建新节点
        new_level = self._random_level()
        
        if new_level > self._level:
            for i in range(self._level + 1, new_level + 1):
                update[i] = self._header
            self._level = new_level
        
        new_node = SkipListNode(value, new_level)
        
        for i in range(new_level + 1):
            new_node._forward[i] = update[i]._forward[i]
            update[i]._forward[i] = new_node
        
        self._size += 1
    
    def search(self, value: Any) -> Optional[Any]:
        """
        搜索值
        
        Args:
            value: 值
            
        Returns:
            值或None
        """
        current = self._header
        
        for i in range(self._level, -1, -1):
            while current._forward[i] and current._forward[i].value < value:
                current = current._forward[i]
            current = current._forward[0]
        
        if current and current.value == value:
            return current.value
        return None
    
    def __contains__(self, value: Any) -> bool:
        return self.search(value) is not None
    
    def erase(self, value: Any) -> bool:
        """
        删除值
        
        Args:
            value: 值
            
        Returns:
            是否成功删除
        """
        update = [None] * (self._max_level + 1)
        current = self._header
        
        for i in range(self._level, -1, -1):
            while current._forward[i] and current._forward[i].value < value:
                current = current._forward[i]
            update[i] = current
        
        current = current._forward[0]
        
        if current is None or current.value != value:
            return False
        
        for i in range(self._level + 1):
            if update[i]._forward[i] != current:
                break
            update[i]._forward[i] = current._forward[i]
        
        # 降低层数
        while self._level > 0 and self._header._forward[self._level] is None:
            self._level -= 1
        
        self._size -= 1
        return True
    
    def to_list(self) -> List:
        """转为列表"""
        result = []
        current = self._header._forward[0]
        while current:
            result.append(current.value)
            current = current._forward[0]
        return result
    
    @property
    def size(self) -> int:
        return self._size
    
    def __len__(self) -> int:
        return self._size
    
    def __str__(self) -> str:
        return str(self.to_list())


# 导出
__all__ = [
    "SkipList",
]
