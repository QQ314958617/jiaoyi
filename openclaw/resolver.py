"""
Resolver - 解析器
基于 Claude Code resolver.ts 设计

依赖解析工具。
"""
from typing import Any, Callable, Dict, List, Set


class Resolver:
    """
    依赖解析器
    
    解析依赖图并确定执行顺序。
    """
    
    def __init__(self):
        self._nodes: Dict[str, Any] = {}
        self._edges: Dict[str, List[str]] = {}
    
    def add_node(self, name: str, value: Any = None) -> None:
        """
        添加节点
        
        Args:
            name: 节点名
            value: 节点值
        """
        self._nodes[name] = value
        if name not in self._edges:
            self._edges[name] = []
    
    def add_dependency(self, name: str, depends_on: str) -> None:
        """
        添加依赖
        
        Args:
            name: 节点名
            depends_on: 依赖的节点名
        """
        if name not in self._edges:
            self._edges[name] = []
        if depends_on not in self._edges:
            self._edges[depends_on] = []
        self._edges[name].append(depends_on)
    
    def resolve(self, start: str) -> List[str]:
        """
        解析依赖顺序
        
        Args:
            start: 起始节点
            
        Returns:
            拓扑排序后的节点列表
        """
        visited: Set[str] = set()
        result: List[str] = []
        
        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            
            for dep in self._edges.get(node, []):
                dfs(dep)
            
            result.append(node)
        
        dfs(start)
        return result
    
    def resolve_all(self) -> List[str]:
        """
        解析所有节点的顺序
        
        Returns:
            拓扑排序后的节点列表
        """
        visited: Set[str] = set()
        result: List[str] = []
        
        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            
            for dep in self._edges.get(node, []):
                dfs(dep)
            
            result.append(node)
        
        for node in self._nodes:
            dfs(node)
        
        return result
    
    def has_cycle(self) -> bool:
        """检查是否有循环依赖"""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for dep in self._edges.get(node, []):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self._nodes:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    def get_node(self, name: str) -> Any:
        """获取节点值"""
        return self._nodes.get(name)


def resolve_dependencies(
    dependencies: Dict[str, List[str]]
) -> List[str]:
    """
    解析依赖顺序
    
    Args:
        dependencies: {节点: [依赖列表]}
        
    Returns:
        拓扑排序后的节点列表
    """
    resolver = Resolver()
    
    for name in dependencies:
        resolver.add_node(name)
    
    for name, deps in dependencies.items():
        for dep in deps:
            resolver.add_dependency(name, dep)
    
    return resolver.resolve_all()


class CircularDependencyError(Exception):
    """循环依赖错误"""
    pass


def resolve_with_cycle_check(
    dependencies: Dict[str, List[str]]
) -> List[str]:
    """
    带循环检查的依赖解析
    
    Raises:
        CircularDependencyError: 存在循环依赖时
    """
    resolver = Resolver()
    
    for name in dependencies:
        resolver.add_node(name)
    
    for name, deps in dependencies.items():
        for dep in deps:
            resolver.add_dependency(name, dep)
    
    if resolver.has_cycle():
        raise CircularDependencyError("Circular dependency detected")
    
    return resolver.resolve_all()


# 导出
__all__ = [
    "Resolver",
    "resolve_dependencies",
    "CircularDependencyError",
    "resolve_with_cycle_check",
]
