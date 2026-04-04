"""
Graph - 图
基于 Claude Code graph.ts 设计

图结构工具。
"""
from typing import Any, Callable, Dict, List, Set, Tuple


class Graph:
    """
    图（邻接表）
    """
    
    def __init__(self, directed: bool = False):
        """
        Args:
            directed: 是否为有向图
        """
        self._directed = directed
        self._adj: Dict[Any, Set] = {}  # 顶点 -> 邻居
    
    def add_vertex(self, v: Any) -> bool:
        """
        添加顶点
        
        Args:
            v: 顶点
            
        Returns:
            是否成功
        """
        if v not in self._adj:
            self._adj[v] = set()
            return True
        return False
    
    def add_edge(self, from_v: Any, to_v: Any) -> bool:
        """
        添加边
        
        Args:
            from_v: 起点
            to_v: 终点
            
        Returns:
            是否成功
        """
        self.add_vertex(from_v)
        self.add_vertex(to_v)
        
        self._adj[from_v].add(to_v)
        if not self._directed:
            self._adj[to_v].add(from_v)
        return True
    
    def remove_edge(self, from_v: Any, to_v: Any) -> bool:
        """
        移除边
        
        Args:
            from_v: 起点
            to_v: 终点
            
        Returns:
            是否成功
        """
        if from_v not in self._adj:
            return False
        
        if to_v in self._adj[from_v]:
            self._adj[from_v].remove(to_v)
            if not self._directed:
                self._adj[to_v].remove(from_v)
            return True
        return False
    
    def remove_vertex(self, v: Any) -> bool:
        """
        移除顶点
        
        Args:
            v: 顶点
            
        Returns:
            是否成功
        """
        if v not in self._adj:
            return False
        
        # 移除所有相关的边
        for neighbor in list(self._adj[v]):
            self.remove_edge(v, neighbor)
            if not self._directed:
                self.remove_edge(neighbor, v)
        
        del self._adj[v]
        return True
    
    def neighbors(self, v: Any) -> Set:
        """获取邻居"""
        return self._adj.get(v, set()).copy()
    
    def vertices(self) -> List:
        """所有顶点"""
        return list(self._adj.keys())
    
    def edges(self) -> List[Tuple]:
        """所有边"""
        result = []
        visited = set()
        
        for from_v, to_set in self._adj.items():
            for to_v in to_set:
                if self._directed or (from_v, to_v) not in visited:
                    result.append((from_v, to_v))
                    visited.add((from_v, to_v))
                    visited.add((to_v, from_v))
        
        return result
    
    def has_path(self, from_v: Any, to_v: Any) -> bool:
        """
        是否有路径
        
        Args:
            from_v: 起点
            to_v: 终点
            
        Returns:
            是否有路径
        """
        if from_v not in self._adj or to_v not in self._adj:
            return False
        
        visited = set()
        queue = [from_v]
        
        while queue:
            current = queue.pop(0)
            if current == to_v:
                return True
            
            if current in visited:
                continue
            visited.add(current)
            
            for neighbor in self._adj[current]:
                if neighbor not in visited:
                    queue.append(neighbor)
        
        return False
    
    def bfs(self, start: Any, visitor: Callable) -> None:
        """
        广度优先遍历
        
        Args:
            start: 起始顶点
            visitor: (vertex) -> None
        """
        if start not in self._adj:
            return
        
        visited = set()
        queue = [start]
        
        while queue:
            v = queue.pop(0)
            if v in visited:
                continue
            visited.add(v)
            visitor(v)
            
            for neighbor in self._adj[v]:
                if neighbor not in visited:
                    queue.append(neighbor)
    
    def dfs(self, start: Any, visitor: Callable) -> None:
        """
        深度优先遍历
        
        Args:
            start: 起始顶点
            visitor: (vertex) -> None
        """
        if start not in self._adj:
            return
        
        visited = set()
        stack = [start]
        
        while stack:
            v = stack.pop()
            if v in visited:
                continue
            visited.add(v)
            visitor(v)
            
            for neighbor in self._adj[v]:
                if neighbor not in visited:
                    stack.append(neighbor)
    
    @property
    def size(self) -> int:
        """顶点数"""
        return len(self._adj)


# 导出
__all__ = [
    "Graph",
]
