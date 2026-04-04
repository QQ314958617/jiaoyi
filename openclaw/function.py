"""
Function - 函数
基于 Claude Code function.ts 设计

函数工具。
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
    arity = fn.__code__.co_argcount
    
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= arity:
            return fn(*args, **kwargs)
        def next_curry(*more_args, **more_kwargs):
            return curried(*args, *more_args, **kwargs, **more_kwargs)
        return next_curry
    
    return curried


def partial(fn: Callable, *preset_args, **preset_kwargs) -> Callable:
    """
    偏函数
    
    Args:
        fn: 函数
        *preset_args: 预设位置参数
        **preset_kwargs: 预设命名参数
        
    Returns:
        偏函数
    """
    def partial_fn(*args, **kwargs):
        return fn(*preset_args, *args, **preset_kwargs, **kwargs)
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


def flip(fn: Callable) -> Callable:
    """
    翻转参数顺序
    
    Args:
        fn: 函数
        
    Returns:
        翻转后的函数
    """
    def flipped(*args, **kwargs):
        return fn(*reversed(args), **kwargs)
    return flipped


def unary(fn: Callable) -> Callable:
    """单参数函数"""
    def unary_fn(arg):
        return fn(arg)
    return unary_fn


def spread(fn: Callable) -> Callable:
    """展开参数数组"""
    def spread_fn(args):
        return fn(*args)
    return spread_fn


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


# 导出
__all__ = [
    "curry",
    "partial",
    "compose",
    "pipe",
    "flip",
    "unary",
    "spread",
    "memoize",
    "once",
]
