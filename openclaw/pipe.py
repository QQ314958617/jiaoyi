"""
Pipe - 管道
基于 Claude Code pipe.ts 设计

管道函数工具。
"""
from typing import Any, Callable


def pipe(*fns: Callable) -> Callable:
    """
    管道函数
    
    pipe(f, g, h)(x) = h(g(f(x)))
    
    Args:
        *fns: 函数列表
        
    Returns:
        管道函数
    """
    def piped(x):
        result = x
        for fn in fns:
            result = fn(result)
        return result
    return piped


def compose(*fns: Callable) -> Callable:
    """
    函数组合
    
    compose(f, g, h)(x) = f(g(h(x)))
    
    Args:
        *fns: 函数列表
        
    Returns:
        组合函数
    """
    def composed(x):
        result = x
        for fn in reversed(fns):
            result = fn(result)
        return result
    return composed


def tap(fn: Callable) -> Callable:
    """
    执行副作用
    
    Args:
        fn: 副作用函数
        
    Returns:
        包装函数
    """
    def tapped(x):
        fn(x)
        return x
    return tapped


def juxt(*fns: Callable) -> Callable:
    """
    并行应用
    
    juxt(f, g, h)(x) = [f(x), g(x), h(x)]
    
    Args:
        *fns: 函数列表
        
    Returns:
        返回结果列表的函数
    """
    def juxtaposed(x):
        return [fn(x) for fn in fns]
    return juxtaposed


def complement(fn: Callable) -> Callable:
    """
    取反函数
    
    complement(fn)(x) = not fn(x)
    """
    def complemented(x):
        return not fn(x)
    return complemented


def identity(x: Any) -> Any:
    """
    恒等函数
    
    Args:
        x: 任何值
        
    Returns:
        相同的值
    """
    return x


def constantly(value: Any) -> Callable:
    """
    常量函数
    
    constantly(x)() = x
    """
    def const(*args, **kwargs):
        return value
    return const


def flip(fn: Callable) -> Callable:
    """
    翻转参数顺序
    """
    def flipped(*args, **kwargs):
        return fn(*reversed(args), **kwargs)
    return flipped


# 导出
__all__ = [
    "pipe",
    "compose",
    "tap",
    "juxt",
    "complement",
    "identity",
    "constantly",
    "flip",
]
