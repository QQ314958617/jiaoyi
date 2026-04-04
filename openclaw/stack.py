"""
Stack - 栈
基于 Claude Code stack.ts 设计

栈数据结构。
"""
from typing import Any, List, Optional


class Stack:
    """
    栈
    """
    
    def __init__(self):
        self._data: List = []
    
    def push(self, item: Any) -> None:
        """压栈"""
        self._data.append(item)
    
    def pop(self) -> Optional[Any]:
        """弹栈"""
        if self._data:
            return self._data.pop()
        return None
    
    def peek(self) -> Optional[Any]:
        """查看栈顶"""
        if self._data:
            return self._data[-1]
        return None
    
    def is_empty(self) -> bool:
        return len(self._data) == 0
    
    def size(self) -> int:
        return len(self._data)
    
    def clear(self) -> None:
        """清空"""
        self._data.clear()
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __iter__(self):
        return reversed(self._data)
    
    def to_list(self) -> List:
        """转为列表"""
        return list(self._data)
    
    def __repr__(self):
        return f"Stack({self._data})"


def balanced(parentheses: str) -> bool:
    """
    检查括号是否平衡
    
    Args:
        parentheses: 括号字符串
        
    Returns:
        是否平衡
    """
    stack = Stack()
    pairs = {')': '(', ']': '[', '}': '{'}
    
    for char in parentheses:
        if char in '([{':
            stack.push(char)
        elif char in ')]}':
            if stack.is_empty():
                return False
            top = stack.pop()
            if top != pairs[char]:
                return False
    
    return stack.is_empty()


def evaluate_postfix(expr: str) -> float:
    """
    后缀表达式求值
    
    Args:
        expr: 后缀表达式（空格分隔）
        
    Returns:
        结果
    """
    stack = Stack()
    ops = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b,
    }
    
    for token in expr.split():
        if token in ops:
            b = stack.pop()
            a = stack.pop()
            stack.push(ops[token](a, b))
        else:
            stack.push(float(token))
    
    return stack.pop()


# 导出
__all__ = [
    "Stack",
    "balanced",
    "evaluate_postfix",
]
