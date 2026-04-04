"""
RBTree - 红黑树
基于 Claude Code rbtree.ts 设计

红黑树实现。
"""
from enum import Enum
from typing import Any, Callable, List, Optional


class Color(Enum):
    RED = True
    BLACK = False


class RBNode:
    """红黑树节点"""
    
    def __init__(self, value: Any, color: Color = Color.RED):
        self.value = value
        self.color = color
        self.left: Optional["RBNode"] = None
        self.right: Optional["RBNode"] = None
        self.parent: Optional["RBNode"] = None


class RBTree:
    """
    红黑树
    
    自平衡二叉搜索树。
    """
    
    def __init__(self, key: Callable = None):
        """
        Args:
            key: 比较键函数
        """
        self._key = key or (lambda x: x)
        self._root: Optional[RBNode] = None
        self._size = 0
    
    def _compare(self, a: Any, b: Any) -> int:
        """比较两个值"""
        ka = self._key(a)
        kb = self._key(b)
        if ka < kb:
            return -1
        elif ka > kb:
            return 1
        return 0
    
    def _rotate_left(self, node: RBNode) -> None:
        """左旋"""
        right = node.right
        node.right = right.left
        
        if right.left:
            right.left.parent = node
        
        right.parent = node.parent
        
        if node.parent is None:
            self._root = right
        elif node == node.parent.left:
            node.parent.left = right
        else:
            node.parent.right = right
        
        right.left = node
        node.parent = right
    
    def _rotate_right(self, node: RBNode) -> None:
        """右旋"""
        left = node.left
        node.left = left.right
        
        if left.right:
            left.right.parent = node
        
        left.parent = node.parent
        
        if node.parent is None:
            self._root = left
        elif node == node.parent.right:
            node.parent.right = left
        else:
            node.parent.left = left
        
        left.right = node
        node.parent = left
    
    def insert(self, value: Any) -> None:
        """
        插入值
        
        Args:
            value: 值
        """
        node = RBNode(value)
        node.left = None
        node.right = None
        node.color = Color.RED
        
        parent = None
        current = self._root
        
        while current:
            parent = current
            if self._compare(node.value, current.value) < 0:
                current = current.left
            else:
                current = current.right
        
        node.parent = parent
        
        if parent is None:
            self._root = node
        elif self._compare(node.value, parent.value) < 0:
            parent.left = node
        else:
            parent.right = node
        
        self._size += 1
        self._insert_fixup(node)
    
    def _insert_fixup(self, node: RBNode) -> None:
        """修正插入后的树"""
        while node.parent and node.parent.color == Color.RED:
            if node.parent == node.parent.parent.left:
                uncle = node.parent.parent.right
                
                if uncle and uncle.color == Color.RED:
                    node.parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self._rotate_left(node)
                    
                    node.parent.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    self._rotate_right(node.parent.parent)
            else:
                uncle = node.parent.parent.left
                
                if uncle and uncle.color == Color.RED:
                    node.parent.color = Color.BLACK
                    uncle.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self._rotate_right(node)
                    
                    node.parent.color = Color.BLACK
                    node.parent.parent.color = Color.RED
                    self._rotate_left(node.parent.parent)
        
        self._root.color = Color.BLACK
    
    def search(self, value: Any) -> Optional[Any]:
        """
        搜索值
        
        Args:
            value: 值
            
        Returns:
            值或None
        """
        current = self._root
        
        while current:
            cmp = self._compare(value, current.value)
            if cmp == 0:
                return current.value
            elif cmp < 0:
                current = current.left
            else:
                current = current.right
        
        return None
    
    def __contains__(self, value: Any) -> bool:
        return self.search(value) is not None
    
    def to_list(self) -> List:
        """中序遍历转为列表"""
        result = []
        self._inorder(self._root, result)
        return result
    
    def _inorder(self, node: Optional[RBNode], result: List) -> None:
        """中序遍历"""
        if node:
            self._inorder(node.left, result)
            result.append(node.value)
            self._inorder(node.right, result)
    
    @property
    def size(self) -> int:
        return self._size
    
    def __len__(self) -> int:
        return self._size


# 导出
__all__ = [
    "RBTree",
]
