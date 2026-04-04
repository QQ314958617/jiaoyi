"""
Router - 路由
基于 Claude Code router.ts 设计

路由工具。
"""
import re
from typing import Callable, Dict, List, Optional, Tuple


class Route:
    """路由"""
    
    def __init__(self, pattern: str, handler: Callable):
        """
        Args:
            pattern: URL模式 (如 "/users/:id")
            handler: 处理函数
        """
        self.pattern = pattern
        self.handler = handler
        self._param_names: List[str] = []
        self._regex: Optional[re.Pattern] = None
        self._compile()
    
    def _compile(self) -> None:
        """编译正则"""
        # 转换 :param 为命名组
        pattern = self.pattern
        param_pattern = r':(\w+)'
        
        def replace_param(match):
            self._param_names.append(match.group(1))
            return r'(?P<' + match.group(1) + '>[^/]+)'
        
        pattern = re.sub(param_pattern, replace_param, pattern)
        pattern = '^' + pattern + '$'
        self._regex = re.compile(pattern)
    
    def match(self, path: str) -> Optional[Dict[str, str]]:
        """
        匹配路径
        
        Args:
            path: URL路径
            
        Returns:
            参数字典或None
        """
        if self._regex is None:
            return None
        
        match = self._regex.match(path)
        if match:
            return match.groupdict()
        return None
    
    def __repr__(self) -> str:
        return f"Route({self.pattern})"


class Router:
    """
    路由
    """
    
    def __init__(self):
        self._routes: List[Route] = []
        self._middleware: List[Callable] = []
    
    def add(self, pattern: str, handler: Callable) -> Route:
        """
        添加路由
        
        Args:
            pattern: URL模式
            handler: 处理函数
            
        Returns:
            Route实例
        """
        route = Route(pattern, handler)
        self._routes.append(route)
        return route
    
    def get(self, pattern: str) -> Callable:
        """添加GET路由"""
        def decorator(fn: Callable) -> Callable:
            self.add(pattern, fn)
            return fn
        return decorator
    
    def post(self, pattern: str) -> Callable:
        """添加POST路由"""
        def decorator(fn: Callable) -> Callable:
            def wrapped(req, res, **kwargs):
                return fn(req, res, **kwargs)
            wrapped.__method__ = 'POST'
            self.add(pattern, wrapped)
            return fn
        return decorator
    
    def use(self, middleware: Callable) -> None:
        """添加中间件"""
        self._middleware.append(middleware)
    
    def match(self, path: str, method: str = 'GET') -> Tuple[Optional[Callable], Dict]:
        """
        匹配路径
        
        Args:
            path: URL路径
            method: HTTP方法
            
        Returns:
            (handler, params) 或 (None, {})
        """
        for route in self._routes:
            params = route.match(path)
            if params is not None:
                handler = route.handler
                
                # 应用中间件
                for mw in self._middleware:
                    handler = mw(handler) or handler
                
                return handler, params
        
        return None, {}


# 导出
__all__ = [
    "Route",
    "Router",
]
