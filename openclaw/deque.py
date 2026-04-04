"""
Deque - 双端队列
基于 Claude Code deque.ts 设计

双端队列数据结构。
"""
from typing import Any, List, Optional


class Deque:
    """
    双端队列
    
    两端都可以插入和删除。
    """
    
    def __init__(self):
        self._data: List = []
    
    # 左侧操作
    def push_left(self, item: Any) -> None:
        """左侧插入"""
        self._data.insert(0, item)
    
    def pop_left(self) -> Optional[Any]:
        """左侧弹出"""
        if self._data:
            return self._data.pop(0)
        return None
    
    def peek_left(self) -> Optional[Any]:
        """查看左侧"""
        if self._data:
            return self._data[0]
        return None
    
    # 右侧操作
    def push_right(self, item: Any) -> None:
        """右侧插入"""
        self._data.append(item)
    
    def pop_right(self) -> Optional[Any]:
        """右侧弹出"""
        if self._data:
            return self._data.pop()
        return None
    
    def peek_right(self) -> Optional[Any]:
        """查看右侧"""
        if self._data:
            return self._data[-1]
        return None
    
    # 别名
    def append(self, item: Any) -> None:
        """右侧插入"""
        self.push_right(item)
    
    def appendleft(self, item: Any) -> None:
        """左侧插入"""
        self.push_left(item)
    
    def popleft(self) -> Optional[Any]:
        """左侧弹出"""
        return self.pop_left()
    
    def pop(self) -> Optional[Any]:
        """右侧弹出"""
        return self.pop_right()
    
    def peek(self) -> Optional[Any]:
        """查看右侧"""
        return self.peek_right()
    
    def peek_front(self) -> Optional[Any]:
        """查看左侧"""
        return self.peek_left()
    
    def peek_back(self) -> Optional[Any]:
        """查看右侧"""
        return self.peek_right()
    
    # 属性
    def is_empty(self) -> bool:
        return len(self._data) == 0
    
    def size(self) -> int:
        return len(self._data)
    
    def clear(self) -> None:
        self._data.clear()
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __iter__(self):
        return iter(self._data)
    
    def to_list(self) -> List:
        return list(self._data)


def rotate_left(deque: Deque, n: int = 1) -> None:
    """
    左旋转
    
    Args:
        deque: 双端队列
        n: 旋转数
    """
    for _ in range(n):
        if not deque.is_empty():
            item = deque.pop_left()
            deque.push_right(item)


def rotate_right(deque: Deque, n: int = 1) -> None:
    """
    右旋转
    
    Args:
        deque: 双端队列
        n: 旋转数
    """
    for _ in range(n):
        if not deque.is_empty():
            item = deque.pop_right()
            deque.push_left(item)


# 导出
__all__ = [
    "Deque",
    "rotate_left",
    "rotate_right",
]
