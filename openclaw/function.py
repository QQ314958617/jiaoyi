"""
Function - 函数工具
基于 Claude Code function.ts 设计

函数式工具。
"""
from typing import Any, Callable


def curry(fn: Callable) -> Callable:
    """
    柯里化
    
    Args:
        fn: 多参数函数
        
    Returns:
        柯里化后的函数
    """
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= fn.__code__.co_argcount:
            return fn(*args, **kwargs)
        def next_curry(*args2, **kwargs2):
            return curried(*args, *args2, **kwargs, **kwargs2)
        return next_curry
    return curried


def partial(fn: Callable, *args, **kwargs) -> Callable:
    """
    偏函数
    
    Args:
        fn: 函数
        *args, **kwargs: 预设参数
        
    Returns:
        偏函数
    """
    def partial_fn(*rest_args, **rest_kwargs):
        return fn(*args, *rest_args, **kwargs, **rest_kwargs)
    return partial_fn


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


def pipe(*fns: Callable) -> Callable:
    """
    管道
    
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


def memoize(fn: Callable) -> Callable:
    """
    记忆化
    
    Args:
        fn: 函数
        
    Returns:
        记忆化函数
    """
    cache = {}
    
    def memoized(*args, **kwargs):
        key = str(args) + str(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = fn(*args, **kwargs)
        return cache[key]
    
    memoized.cache = cache
    return memoized


def once(fn: Callable) -> Callable:
    """
    只执行一次
    
    Args:
        fn: 函数
        
    Returns:
        单次函数
    """
    called = [False]
    result = [None]
    
    def wrapper(*args, **kwargs):
        if not called[0]:
            called[0] = True
            result[0] = fn(*args, **kwargs)
        return result[0]
    
    return wrapper


def flip(fn: Callable) -> Callable:
    """
    翻转参数
    
    Args:
        fn: 函数
        
    Returns:
        翻转函数
    """
    def flipped(*args, **kwargs):
        return fn(*reversed(args), **kwargs)
    return flipped


def unary(fn: Callable) -> Callable:
    """
    单参数函数
    
    Args:
        fn: 函数
        
    Returns:
        只接收第一个参数的函数
    """
    def unary_fn(arg):
        return fn(arg)
    return unary_fn


def spread(fn: Callable) -> Callable:
    """
    展开参数
    
    Args:
        fn: 函数
        
    Returns:
        接受数组并展开的函数
    """
    def spread_fn(args):
        return fn(*args)
    return spread_fn


# 导出
__all__ = [
    "curry",
    "partial",
    "compose",
    "pipe",
    "memoize",
    "once",
    "flip",
    "unary",
    "spread",
]
