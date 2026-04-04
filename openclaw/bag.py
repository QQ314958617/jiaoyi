"""
Bag - 背包
基于 Claude Code bag.ts 设计

背包/多集合工具。
"""
from typing import Any, Dict, Iterator, List


class Bag:
    """
    背包/多集合
    
    允许重复元素的集合。
    """
    
    def __init__(self):
        self._items: Dict[Any, int] = {}
        self._size = 0
    
    def add(self, item: Any, count: int = 1) -> None:
        """
        添加
        
        Args:
            item: 元素
            count: 数量
        """
        self._items[item] = self._items.get(item, 0) + count
        self._size += count
    
    def remove(self, item: Any, count: int = 1) -> bool:
        """
        移除
        
        Args:
            item: 元素
            count: 数量
            
        Returns:
            是否成功
        """
        if item not in self._items:
            return False
        
        current = self._items[item]
        if count >= current:
            del self._items[item]
            self._size -= current
        else:
            self._items[item] = current - count
            self._size -= count
        
        return True
    
    def count(self, item: Any) -> int:
        """获取元素数量"""
        return self._items.get(item, 0)
    
    def contains(self, item: Any) -> bool:
        """检查是否包含"""
        return item in self._items
    
    def is_empty(self) -> bool:
        return self._size == 0
    
    def clear(self) -> None:
        """清空"""
        self._items.clear()
        self._size = 0
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, item: Any) -> bool:
        return item in self._items
    
    def __iter__(self) -> Iterator:
        """迭代（每个元素单独返回）"""
        for item, count in self._items.items():
            for _ in range(count):
                yield item
    
    def items(self) -> List[tuple]:
        """返回(item, count)列表"""
        return list(self._items.items())
    
    def unique(self) -> List:
        """唯一元素列表"""
        return list(self._items.keys())
    
    def union(self, other: "Bag") -> "Bag":
        """并集"""
        result = Bag()
        for item, count in self._items.items():
            result.add(item, count)
        for item, count in other._items.items():
            result.add(item, count)
        return result
    
    def intersection(self, other: "Bag") -> "Bag":
        """交集"""
        result = Bag()
        for item, count in self._items.items():
            if item in other._items:
                result.add(item, min(count, other._items[item]))
        return result
    
    def difference(self, other: "Bag") -> "Bag":
        """差集"""
        result = Bag()
        for item, count in self._items.items():
            if item not in other._items:
                result.add(item, count)
            else:
                diff = count - other._items[item]
                if diff > 0:
                    result.add(item, diff)
        return result


# 导出
__all__ = [
    "Bag",
]
