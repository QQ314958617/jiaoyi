"""
Tree - 树
基于 Claude Code tree.ts 设计

二叉树和相关算法。
"""
from typing import Any, Callable, Generic, List, Optional, TypeVar
from collections import deque

T = TypeVar('T')


class TreeNode(Generic[T]):
    """树节点"""
    
    def __init__(
        self,
        value: T,
        left: Optional["TreeNode[T]"] = None,
        right: Optional["TreeNode[T]"] = None,
    ):
        self.value = value
        self.left = left
        self.right = right


class BinaryTree(Generic[T]):
    """
    二叉树
    
    支持遍历、搜索等操作。
    """
    
    def __init__(self, root: Optional[TreeNode[T]] = None):
        self._root = root
    
    @classmethod
    def from_list(cls, items: List[T]) -> "BinaryTree[T]":
        """从列表构建树（层序）"""
        if not items:
            return cls()
        
        root = TreeNode(items[0])
        queue = deque([root])
        i = 1
        
        while queue and i < len(items):
            node = queue.popleft()
            
            # 左子节点
            if i < len(items):
                node.left = TreeNode(items[i])
                queue.append(node.left)
                i += 1
            
            # 右子节点
            if i < len(items):
                node.right = TreeNode(items[i])
                queue.append(node.right)
                i += 1
        
        return cls(root)
    
    def is_empty(self) -> bool:
        """是否为空"""
        return self._root is None
    
    def preorder(self, visit: Callable[[T], None]) -> None:
        """前序遍历"""
        def _visit(node: Optional[TreeNode[T]]):
            if node is None:
                return
            visit(node.value)
            _visit(node.left)
            _visit(node.right)
        
        _visit(self._root)
    
    def inorder(self, visit: Callable[[T], None]) -> None:
        """中序遍历"""
        def _visit(node: Optional[TreeNode[T]]):
            if node is None:
                return
            _visit(node.left)
            visit(node.value)
            _visit(node.right)
        
        _visit(self._root)
    
    def postorder(self, visit: Callable[[T], None]) -> None:
        """后序遍历"""
        def _visit(node: Optional[TreeNode[T]]):
            if node is None:
                return
            _visit(node.left)
            _visit(node.right)
            visit(node.value)
        
        _visit(self._root)
    
    def level_order(self, visit: Callable[[T], None]) -> None:
        """层序遍历"""
        if self._root is None:
            return
        
        queue = deque([self._root])
        
        while queue:
            node = queue.popleft()
            visit(node.value)
            
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
    
    def height(self) -> int:
        """树高度"""
        def _height(node: Optional[TreeNode[T]]) -> int:
            if node is None:
                return 0
            return 1 + max(_height(node.left), _height(node.right))
        
        return _height(self._root)
    
    def find(self, value: T) -> bool:
        """查找值"""
        if self._root is None:
            return False
        
        queue = deque([self._root])
        
        while queue:
            node = queue.popleft()
            if node.value == value:
                return True
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        
        return False


class TrieNode:
    """字典树节点"""
    
    def __init__(self):
        self._children: dict = {}
        self._is_end: bool = False


class Trie:
    """
    字典树（前缀树）
    
    高效存储和搜索字符串。
    """
    
    def __init__(self):
        self._root = TrieNode()
    
    def insert(self, word: str) -> None:
        """插入单词"""
        node = self._root
        
        for char in word:
            if char not in node._children:
                node._children[char] = TrieNode()
            node = node._children[char]
        
        node._is_end = True
    
    def search(self, word: str) -> bool:
        """搜索单词"""
        node = self._find_node(word)
        return node is not None and node._is_end
    
    def starts_with(self, prefix: str) -> bool:
        """检查前缀"""
        return self._find_node(prefix) is not None
    
    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """查找前缀对应的节点"""
        node = self._root
        
        for char in prefix:
            if char not in node._children:
                return None
            node = node._children[char]
        
        return node


# 导出
__all__ = [
    "TreeNode",
    "BinaryTree",
    "TrieNode",
    "Trie",
]
