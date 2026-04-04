"""
Tree - 树
基于 Claude Code tree.ts 设计

树结构工具。
"""
from typing import Any, Callable, List, Optional


class TreeNode:
    """
    树节点
    """
    
    def __init__(self, value: Any, children: List["TreeNode"] = None):
        """
        Args:
            value: 节点值
            children: 子节点列表
        """
        self.value = value
        self.children = children or []
        self._parent: Optional["TreeNode"] = None
    
    def add_child(self, node: "TreeNode") -> "TreeNode":
        """添加子节点"""
        node._parent = self
        self.children.append(node)
        return node
    
    def remove_child(self, node: "TreeNode") -> bool:
        """移除子节点"""
        if node in self.children:
            node._parent = None
            self.children.remove(node)
            return True
        return False
    
    @property
    def parent(self) -> Optional["TreeNode"]:
        return self._parent
    
    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0
    
    @property
    def is_root(self) -> bool:
        return self._parent is None
    
    def depth(self) -> int:
        """节点深度"""
        depth = 0
        node = self._parent
        while node:
            depth += 1
            node = node._parent
        return depth
    
    def height(self) -> int:
        """节点高度"""
        if self.is_leaf:
            return 1
        return 1 + max(child.height() for child in self.children)
    
    def ancestors(self) -> List["TreeNode"]:
        """祖先节点"""
        result = []
        node = self._parent
        while node:
            result.append(node)
            node = node._parent
        return result
    
    def descendants(self) -> List["TreeNode"]:
        """后代节点"""
        result = []
        stack = list(self.children)
        while stack:
            node = stack.pop()
            result.append(node)
            stack.extend(node.children)
        return result


class Tree:
    """
    树
    """
    
    def __init__(self, root: TreeNode = None):
        """
        Args:
            root: 根节点
        """
        self._root = root
    
    @property
    def root(self) -> TreeNode:
        return self._root
    
    def height(self) -> int:
        """树高度"""
        if self._root is None:
            return 0
        return self._root.height()
    
    def size(self) -> int:
        """节点数"""
        if self._root is None:
            return 0
        return 1 + len(self._root.descendants())
    
    def traverse(self, fn: Callable, mode: str = "breadth") -> None:
        """
        遍历树
        
        Args:
            fn: (node) -> None
            mode: "breadth"或"depth"
        """
        if self._root is None:
            return
        
        if mode == "breadth":
            queue = [self._root]
            while queue:
                node = queue.pop(0)
                fn(node)
                queue.extend(node.children)
        else:
            stack = [self._root]
            while stack:
                node = stack.pop()
                fn(node)
                stack.extend(reversed(node.children))
    
    def find(self, predicate: Callable) -> Optional[TreeNode]:
        """
        查找节点
        
        Args:
            predicate: (node) -> bool
            
        Returns:
            第一个匹配的节点或None
        """
        if self._root is None:
            return None
        
        queue = [self._root]
        while queue:
            node = queue.pop(0)
            if predicate(node):
                return node
            queue.extend(node.children)
        return None


# 导出
__all__ = [
    "TreeNode",
    "Tree",
]
