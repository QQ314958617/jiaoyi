"""
Middleware - 中间件
基于 Claude Code middleware.ts 设计

中间件模式工具。
"""
from typing import Any, Callable, List


Middleware = Callable[[Callable], Callable]


class MiddlewareChain:
    """
    中间件链
    
    组合多个中间件。
    """
    
    def __init__(self):
        self._middlewares: List[Middleware] = []
    
    def use(self, middleware: Middleware) -> "MiddlewareChain":
        """
        添加中间件
        
        Args:
            middleware: 中间件函数
            
        Returns:
            self
        """
        self._middlewares.append(middleware)
        return self
    
    def compose(self) -> Callable:
        """
        组合中间件
        
        Returns:
            组合后的函数
        """
        if not self._middlewares:
            return lambda x: x
        
        def composed(context: Any = None) -> Any:
            index = [0]  # 用列表包装以便在内部修改
            
            def dispatch(i: int) -> Any:
                if i >= len(self._middlewares):
                    return context
                
                middleware = self._middlewares[i]
                
                def next_handler():
                    return dispatch(i + 1)
                
                return middleware(next_handler)(context)
            
            return dispatch(0)
        
        return composed
    
    def execute(self, context: Any = None) -> Any:
        """
        执行链
        
        Args:
            context: 初始上下文
            
        Returns:
            最终结果
        """
        return self.compose()(context)
    
    def clear(self) -> None:
        """清空中间件"""
        self._middlewares.clear()


def create_middleware(
    before: Callable = None,
    after: Callable = None,
) -> Middleware:
    """
    创建中间件
    
    Args:
        before: 执行前回调
        after: 执行后回调
        
    Returns:
        中间件函数
    """
    def middleware(next_handler: Callable) -> Callable:
        def handler(context: Any = None) -> Any:
            if before:
                before(context)
            
            result = next_handler()
            
            if after:
                after(context)
            
            return result
        
        return handler
    
    return middleware


def logger_middleware(next_handler: Callable) -> Callable:
    """日志中间件"""
    def handler(*args, **kwargs):
        print(f"[Middleware] Before handler")
        result = next_handler()
        print(f"[Middleware] After handler")
        return result
    return handler


def timing_middleware(next_handler: Callable) -> Callable:
    """计时中间件"""
    import time
    
    def handler(*args, **kwargs):
        start = time.time()
        result = next_handler()
        elapsed = time.time() - start
        print(f"[Timing] {elapsed:.3f}s")
        return result
    return handler


def error_handler_middleware(
    next_handler: Callable,
    error_handler: Callable[[Exception], Any],
) -> Callable:
    """错误处理中间件"""
    def handler(*args, **kwargs):
        try:
            return next_handler()
        except Exception as e:
            return error_handler(e)
    return handler


# 导出
__all__ = [
    "Middleware",
    "MiddlewareChain",
    "create_middleware",
    "logger_middleware",
    "timing_middleware",
    "error_handler_middleware",
]
