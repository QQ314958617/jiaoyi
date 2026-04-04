"""
Ring - 环
基于 Claude Code ring.ts 设计

循环链表实现。
"""
from typing import Any, Iterator, Optional


class RingNode:
    """环节点"""
    
    def __init__(self, value: Any):
        self.value = value
        self.next: Optional["RingNode"] = None
        self.prev: Optional["RingNode"] = None


class Ring:
    """
    循环链表
    
    环形数据结构。
    """
    
    def __init__(self):
        self._current: Optional[RingNode] = None
        self._size = 0
    
    def add(self, value: Any) -> None:
        """
        添加节点
        
        Args:
            value: 值
        """
        node = RingNode(value)
        
        if self._size == 0:
            node.next = node
            node.prev = node
            self._current = node
        else:
            # 在当前节点后插入
            node.next = self._current.next
            node.prev = self._current
            self._current.next.prev = node
            self._current.next = node
        
        self._size += 1
    
    def remove(self) -> Optional[Any]:
        """
        移除当前节点
        
        Returns:
            被移除节点的值
        """
        if self._size == 0:
            return None
        
        node = self._current
        value = node.value
        
        if self._size == 1:
            self._current = None
        else:
            node.prev.next = node.next
            node.next.prev = node.prev
            self._current = node.next
        
        self._size -= 1
        return value
    
    def current(self) -> Optional[Any]:
        """获取当前节点值"""
        if self._current:
            return self._current.value
        return None
    
    def next(self) -> Optional[Any]:
        """移动到下一个节点"""
        if self._current:
            self._current = self._current.next
            return self._current.value
        return None
    
    def prev(self) -> Optional[Any]:
        """移动到上一个节点"""
        if self._current:
            self._current = self._current.prev
            return self._current.value
        return None
    
    def rotate(self, steps: int) -> None:
        """
        旋转
        
        Args:
            steps: 步数（正数向后，负数向前）
        """
        if self._size == 0:
            return
        
        for _ in range(abs(steps)):
            if steps > 0:
                self._current = self._current.next
            else:
                self._current = self._current.prev
    
    @property
    def size(self) -> int:
        return self._size
    
    def is_empty(self) -> bool:
        return self._size == 0
    
    def to_list(self) -> list:
        """转为列表"""
        if self._size == 0:
            return []
        
        result = []
        node = self._current
        for _ in range(self._size):
            result.append(node.value)
            node = node.next
        return result
    
    def __iter__(self) -> Iterator:
        return iter(self.to_list())
    
    def __len__(self) -> int:
        return self._size


# 导出
__all__ = [
    "Ring",
]
