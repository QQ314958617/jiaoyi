"""
Trie - 字典树
基于 Claude Code trie.ts 设计

前缀树实现。
"""
from typing import Any, Dict, List, Optional


class TrieNode:
    """字典树节点"""
    
    def __init__(self):
        self._children: Dict[str, TrieNode] = {}
        self._is_end: bool = False
        self._value: Any = None


class Trie:
    """
    字典树（前缀树）
    
    高效存储和搜索字符串。
    """
    
    def __init__(self):
        self._root = TrieNode()
        self._size = 0
    
    def insert(self, word: str, value: Any = None) -> None:
        """
        插入单词
        
        Args:
            word: 单词
            value: 关联值
        """
        node = self._root
        
        for char in word:
            if char not in node._children:
                node._children[char] = TrieNode()
            node = node._children[char]
        
        if not node._is_end:
            self._size += 1
        
        node._is_end = True
        node._value = value
    
    def search(self, word: str) -> bool:
        """
        搜索单词
        
        Args:
            word: 单词
            
        Returns:
            是否存在
        """
        node = self._find_node(word)
        return node is not None and node._is_end
    
    def starts_with(self, prefix: str) -> bool:
        """
        检查前缀
        
        Args:
            prefix: 前缀
            
        Returns:
            是否有此前缀
        """
        return self._find_node(prefix) is not None
    
    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """查找前缀对应的节点"""
        node = self._root
        
        for char in prefix:
            if char not in node._children:
                return None
            node = node._children[char]
        
        return node
    
    def get(self, word: str) -> Any:
        """
        获取单词关联的值
        
        Args:
            word: 单词
            
        Returns:
            关联值或None
        """
        node = self._find_node(word)
        if node and node._is_end:
            return node._value
        return None
    
    def delete(self, word: str) -> bool:
        """
        删除单词
        
        Args:
            word: 单词
            
        Returns:
            是否成功删除
        """
        def _delete(node: TrieNode, index: int) -> bool:
            if index == len(word):
                if not node._is_end:
                    return False
                node._is_end = False
                node._value = None
                return len(node._children) == 0
            
            char = word[index]
            if char not in node._children:
                return False
            
            child = node._children[char]
            should_delete_child = _delete(child, index + 1)
            
            if should_delete_child:
                del node._children[char]
                return len(node._children) == 0 and not node._is_end
            
            return False
        
        if self.search(word):
            _delete(self._root, 0)
            self._size -= 1
            return True
        return False
    
    def words_with_prefix(self, prefix: str) -> List[str]:
        """
        获取前缀匹配的所有单词
        
        Args:
            prefix: 前缀
            
        Returns:
            匹配的单词列表
        """
        node = self._find_node(prefix)
        if not node:
            return []
        
        results = []
        self._collect_words(node, prefix, results)
        return results
    
    def _collect_words(
        self,
        node: TrieNode,
        prefix: str,
        results: List[str],
    ) -> None:
        """收集所有单词"""
        if node._is_end:
            results.append(prefix)
        
        for char, child in node._children.items():
            self._collect_words(child, prefix + char, results)
    
    @property
    def size(self) -> int:
        """单词数量"""
        return self._size
    
    def __len__(self) -> int:
        return self._size
    
    def __contains__(self, word: str) -> bool:
        return self.search(word)


# 导出
__all__ = [
    "Trie",
    "TrieNode",
]
