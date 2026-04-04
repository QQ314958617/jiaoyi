"""
Counter - 计数器
基于 Claude Code counter.ts 设计

计数器工具。
"""
from typing import Any, Callable, Dict


class Counter:
    """
    计数器
    
    统计出现次数。
    """
    
    def __init__(self):
        self._counts: Dict[Any, int] = {}
    
    def inc(self, key: Any, amount: int = 1) -> int:
        """
        增加计数
        
        Args:
            key: 键
            amount: 增量
            
        Returns:
            当前计数
        """
        self._counts[key] = self._counts.get(key, 0) + amount
        return self._counts[key]
    
    def dec(self, key: Any, amount: int = 1) -> int:
        """
        减少计数
        
        Args:
            key: 键
            amount: 减量
            
        Returns:
            当前计数
        """
        return self.inc(key, -amount)
    
    def get(self, key: Any) -> int:
        """获取计数"""
        return self._counts.get(key, 0)
    
    def set(self, key: Any, value: int) -> None:
        """设置计数"""
        self._counts[key] = value
    
    def reset(self, key: Any = None) -> None:
        """重置"""
        if key:
            self._counts[key] = 0
        else:
            self._counts.clear()
    
    def items(self) -> Dict[Any, int]:
        """所有计数"""
        return dict(self._counts)
    
    def most_common(self, n: int = None) -> list:
        """
        最常见的
        
        Args:
            n: 返回数量
            
        Returns:
            [(key, count)] 列表
        """
        sorted_items = sorted(self._counts.items(), key=lambda x: -x[1])
        if n:
            sorted_items = sorted_items[:n]
        return sorted_items
    
    def total(self) -> int:
        """总数"""
        return sum(self._counts.values())
    
    @property
    def size(self) -> int:
        return len(self._counts)


def count(items: list, key: Callable = None) -> Counter:
    """
    统计列表项
    
    Args:
        items: 列表
        key: 键函数
        
    Returns:
        Counter实例
    """
    counter = Counter()
    
    for item in items:
        k = key(item) if key else item
        counter.inc(k)
    
    return counter


# 导出
__all__ = [
    "Counter",
    "count",
]
