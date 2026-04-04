"""
Graph - 图
基于 Claude Code graph.ts 设计

图数据结构和相关算法。
"""
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar
from collections import deque

T = TypeVar('T')


class Graph(Generic[T]):
    """
    图
    
    使用邻接表实现。
    """
    
    def __init__(self, directed: bool = False):
        """
        Args:
            directed: 是否为有向图
        """
        self._directed = directed
        self._adj: Dict[T, List[T]] = {}
    
    def add_vertex(self, v: T) -> None:
        """添加顶点"""
        if v not in self._adj:
            self._adj[v] = []
    
    def add_edge(self, v: T, w: T) -> None:
        """添加边"""
        self.add_vertex(v)
        self.add_vertex(w)
        self._adj[v].append(w)
        
        if not self._directed:
            self._adj[w].append(v)
    
    def remove_edge(self, v: T, w: T) -> None:
        """移除边"""
        if v in self._adj and w in self._adj[v]:
            self._adj[v].remove(w)
        
        if not self._directed:
            if w in self._adj and v in self._adj[w]:
                self._adj[w].remove(v)
    
    def neighbors(self, v: T) -> List[T]:
        """获取邻居"""
        return self._adj.get(v, [])
    
    def vertices(self) -> List[T]:
        """获取所有顶点"""
        return list(self._adj.keys())
    
    def bfs(self, start: T, visit: Callable[[T], None]) -> None:
        """广度优先搜索"""
        visited: Set[T] = set()
        queue = deque([start])
        
        while queue:
            v = queue.popleft()
            
            if v in visited:
                continue
            
            visited.add(v)
            visit(v)
            
            for neighbor in self.neighbors(v):
                if neighbor not in visited:
                    queue.append(neighbor)
    
    def dfs(self, start: T, visit: Callable[[T], None]) -> None:
        """深度优先搜索"""
        visited: Set[T] = set()
        
        def _dfs(v: T):
            if v in visited:
                return
            
            visited.add(v)
            visit(v)
            
            for neighbor in self.neighbors(v):
                if neighbor not in visited:
                    _dfs(neighbor)
        
        _dfs(start)
    
    def has_path(self, start: T, end: T) -> bool:
        """检查是否存在路径"""
        visited: Set[T] = set()
        queue = deque([start])
        
        while queue:
            v = queue.popleft()
            
            if v == end:
                return True
            
            if v in visited:
                continue
            
            visited.add(v)
            
            for neighbor in self.neighbors(v):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        return False
    
    def topological_sort(self) -> List[T]:
        """拓扑排序"""
        if not self._directed:
            raise ValueError("Topological sort requires directed graph")
        
        in_degree: Dict[T, int] = {v: 0 for v in self._adj}
        
        for v in self._adj:
            for neighbor in self._adj[v]:
                in_degree[neighbor] += 1
        
        queue = deque([v for v, deg in in_degree.items() if deg == 0])
        result = []
        
        while queue:
            v = queue.popleft()
            result.append(v)
            
            for neighbor in self._adj[v]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result


class UnionFind:
    """
    并查集
    
    支持不相交集合的合并和查询。
    """
    
    def __init__(self):
        self._parent: Dict[Any, Any] = {}
        self._rank: Dict[Any, int] = {}
    
    def make_set(self, x: Any) -> None:
        """创建单元素集合"""
        if x not in self._parent:
            self._parent[x] = x
            self._rank[x] = 0
    
    def find(self, x: Any) -> Any:
        """查找根节点（路径压缩）"""
        if x not in self._parent:
            self.make_set(x)
        
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])
        
        return self._parent[x]
    
    def union(self, x: Any, y: Any) -> None:
        """合并集合（按秩合并）"""
        root_x = self.find(x)
        root_y = self.find(y)
        
        if root_x == root_y:
            return
        
        if self._rank[root_x] < self._rank[root_y]:
            self._parent[root_x] = root_y
        elif self._rank[root_x] > self._rank[root_y]:
            self._parent[root_y] = root_x
        else:
            self._parent[root_y] = root_x
            self._rank[root_x] += 1
    
    def connected(self, x: Any, y: Any) -> bool:
        """检查是否连通"""
        return self.find(x) == self.find(y)


# 导出
__all__ = [
    "Graph",
    "UnionFind",
]
