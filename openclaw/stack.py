"""
Stack - 栈
基于 Claude Code stack.ts 设计

栈数据结构实现。
"""
from typing import Generic, List, TypeVar

T = TypeVar('T')


class Stack(Generic[T]):
    """
    栈
    
    后进先出（LIFO）数据结构。
    """
    
    def __init__(self):
        self._items: List[T] = []
    
    def push(self, item: T) -> None:
        """压入栈"""
        self._items.append(item)
    
    def pop(self) -> T:
        """弹出栈顶"""
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()
    
    def peek(self) -> T:
        """查看栈顶"""
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]
    
    def is_empty(self) -> bool:
        """是否为空"""
        return len(self._items) == 0
    
    def size(self) -> int:
        """栈大小"""
        return len(self._items)
    
    def clear(self) -> None:
        """清空栈"""
        self._items.clear()
    
    def __len__(self) -> int:
        return len(self._items)
    
    def __bool__(self) -> bool:
        return bool(self._items)
    
    def __repr__(self) -> str:
        return f"Stack({self._items!r})"


class MinStack(Generic[T]):
    """
    支持获取最小值的栈
    
    所有操作都是O(1)。
    """
    
    def __init__(self):
        self._items: List[T] = []
        self._min_items: List[T] = []
    
    def push(self, item: T) -> None:
        """压入栈"""
        self._items.append(item)
        
        if not self._min_items or item <= self._min_items[-1]:
            self._min_items.append(item)
    
    def pop(self) -> T:
        """弹出栈顶"""
        if not self._items:
            raise IndexError("pop from empty stack")
        
        item = self._items.pop()
        
        if item == self._min_items[-1]:
            self._min_items.pop()
        
        return item
    
    def peek(self) -> T:
        """查看栈顶"""
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]
    
    def get_min(self) -> T:
        """获取最小值"""
        if not self._min_items:
            raise IndexError("get_min from empty stack")
        return self._min_items[-1]
    
    def is_empty(self) -> bool:
        """是否为空"""
        return len(self._items) == 0
    
    def size(self) -> int:
        """栈大小"""
        return len(self._items)


class TwoStacks(Generic[T]):
    """
    双栈队列
    
    用两个栈实现队列（先进先出）。
    """
    
    def __init__(self):
        self._in_stack: Stack = Stack()
        self._out_stack: Stack = Stack()
    
    def enqueue(self, item: T) -> None:
        """入队"""
        self._in_stack.push(item)
    
    def dequeue(self) -> T:
        """出队"""
        if self._out_stack.is_empty():
            while not self._in_stack.is_empty():
                self._out_stack.push(self._in_stack.pop())
        
        if self._out_stack.is_empty():
            raise IndexError("dequeue from empty queue")
        
        return self._out_stack.pop()
    
    def peek(self) -> T:
        """查看队首"""
        if self._out_stack.is_empty():
            while not self._in_stack.is_empty():
                self._out_stack.push(self._in_stack.pop())
        
        if self._out_stack.is_empty():
            raise IndexError("peek from empty queue")
        
        return self._out_stack.peek()
    
    def is_empty(self) -> bool:
        """是否为空"""
        return self._in_stack.is_empty() and self._out_stack.is_empty()
    
    def size(self) -> int:
        """队列大小"""
        return self._in_stack.size() + self._out_stack.size()


# 导出
__all__ = [
    "Stack",
    "MinStack",
    "TwoStacks",
]
