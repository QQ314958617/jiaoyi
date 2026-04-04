"""
Trie - 字典树
基于 Claude Code trie.ts 设计

字典树（Trie）实现。
"""
from typing import Dict, List, Optional, Set


class TrieNode:
    """Trie节点"""
    
    def __init__(self):
        self._children: Dict[str, TrieNode] = {}
        self._is_end: bool = False
        self._value: any = None


class Trie:
    """
    字典树
    
    高效的字符串检索结构。
    """
    
    def __init__(self):
        self._root = TrieNode()
        self._size = 0
    
    def insert(self, word: str, value: any = None) -> None:
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
    
    def search(self, word: str) -> Optional[any]:
        """
        搜索完整单词
        
        Args:
            word: 单词
            
        Returns:
            关联值或None
        """
        node = self._search_prefix(word)
        if node and node._is_end:
            return node._value
        return None
    
    def _search_prefix(self, prefix: str) -> Optional[TrieNode]:
        """搜索前缀"""
        node = self._root
        
        for char in prefix:
            if char not in node._children:
                return None
            node = node._children[char]
        
        return node
    
    def starts_with(self, prefix: str) -> bool:
        """
        检查是否有此前缀
        
        Args:
            prefix: 前缀
            
        Returns:
            是否存在
        """
        return self._search_prefix(prefix) is not None
    
    def words_with_prefix(self, prefix: str) -> List[str]:
        """
        获取指定前缀的所有单词
        
        Args:
            prefix: 前缀
            
        Returns:
            单词列表
        """
        node = self._search_prefix(prefix)
        if node is None:
            return []
        
        result = []
        self._collect_words(node, prefix, result)
        return result
    
    def _collect_words(self, node: TrieNode, prefix: str, result: List) -> None:
        """递归收集单词"""
        if node._is_end:
            result.append(prefix)
        
        for char, child in node._children.items():
            self._collect_words(child, prefix + char, result)
    
    def remove(self, word: str) -> bool:
        """
        删除单词
        
        Args:
            word: 单词
            
        Returns:
            是否成功删除
        """
        node = self._root
        path = [node]
        
        for char in word:
            if char not in node._children:
                return False
            node = node._children[char]
            path.append(node)
        
        if not node._is_end:
            return False
        
        node._is_end = False
        node._value = None
        self._size -= 1
        
        # 清理空叶子节点
        for i in range(len(path) - 2, -1, -1):
            current = path[i]
            char = word[i]
            child = path[i + 1]
            
            if child._is_end or child._children:
                break
            
            del current._children[char]
        
        return True
    
    def autocomplete(self, prefix: str, limit: int = 10) -> List[str]:
        """
        自动补全
        
        Args:
            prefix: 前缀
            limit: 返回数量限制
            
        Returns:
            建议列表
        """
        words = self.words_with_prefix(prefix)
        return words[:limit]
    
    @property
    def size(self) -> int:
        """单词数"""
        return self._size
    
    def __contains__(self, word: str) -> bool:
        return self.search(word) is not None


# 导出
__all__ = [
    "Trie",
]
