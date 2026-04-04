"""
Functools - 函数式工具
基于 Claude Code functools.ts 设计

函数式编程工具。
"""
from typing import Any, Callable, TypeVar

T = TypeVar('T')
U = TypeVar('U')


def compose(*funcs: Callable) -> Callable:
    """
    函数组合
    
    compose(f, g, h)(x) = f(g(h(x)))
    
    Args:
        *funcs: 函数列表
        
    Returns:
        组合函数
    """
    def composed(*args, **kwargs):
        result = funcs[-1](*args, **kwargs)
        for func in reversed(funcs[:-1]):
            result = func(result)
        return result
    return composed


def pipe(*funcs: Callable) -> Callable:
    """
    管道函数
    
    pipe(f, g, h)(x) = h(g(f(x)))
    
    Args:
        *funcs: 函数列表
        
    Returns:
        管道函数
    """
    def piped(*args, **kwargs):
        result = funcs[0](*args, **kwargs)
        for func in funcs[1:]:
            result = func(result)
        return result
    return piped


def curry(func: Callable) -> Callable:
    """
    柯里化
    
    Args:
        func: 要柯里化的函数
        
    Returns:
        柯里化后的函数
    """
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= func.__code__.co_argcount:
            return func(*args, **kwargs)
        def next_curry(*args2, **kwargs2):
            return curried(*(args + args2), **(kwargs | kwargs2))
        return next_curry
    return curried


def memoize(func: Callable) -> Callable:
    """
    记忆化
    
    Args:
        func: 要记忆化的函数
        
    Returns:
        记忆化后的函数
    """
    cache = {}
    
    def memoized(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    
    memoized.cache = cache
    return memoized


def flip(func: Callable) -> Callable:
    """
    翻转参数顺序
    
    Args:
        func: 函数
        
    Returns:
        翻转后的函数
    """
    def flipped(*args, **kwargs):
        return func(*reversed(args), **kwargs)
    return flipped


def negate(func: Callable) -> Callable:
    """
    取反函数
    
    Args:
        func: 函数
        
    Returns:
        取反函数
    """
    def negated(*args, **kwargs):
        return not func(*args, **kwargs)
    return negated


def identity(x: T) -> T:
    """
    恒等函数
    
    Args:
        x: 任何值
        
    Returns:
        相同的值
    """
    return x


def constant(x: T) -> Callable:
    """
    常量函数
    
    Args:
        x: 常量值
        
    Returns:
        返回常量的函数
    """
    def const(*args, **kwargs):
        return x
    return const


def tap(func: Callable) -> Callable:
    """
    执行副作用并返回值
    
    Args:
        func: 副作用函数
        
    Returns:
        包装函数
    """
    def tapped(x):
        func(x)
        return x
    return tapped


# 导出
__all__ = [
    "compose",
    "pipe",
    "curry",
    "memoize",
    "flip",
    "negate",
    "identity",
    "constant",
    "tap",
]
