"""
Util - 通用工具
基于 Claude Code util.ts 设计

通用工具。
"""
import time
from typing import Any, Callable


def noop(*args, **kwargs):
    """空函数"""
    pass


def identity(x: Any) -> Any:
    """恒等函数"""
    return x


def constant(x: Any) -> Callable:
    """常量函数"""
    return lambda *args, **kwargs: x


def always(x: Any) -> Callable:
    """总是返回x"""
    return lambda *args, **kwargs: x


def never(*args, **kwargs) -> bool:
    """总是返回False"""
    return False


def always_true(*args, **kwargs) -> bool:
    """总是返回True"""
    return True


def default_to(default: Any) -> Callable:
    """默认值函数"""
    def wrapper(value):
        return default if value is None else value
    return wrapper


def tap(fn: Callable) -> Callable:
    """执行副作用并返回原值"""
    def tapped(x):
        fn(x)
        return x
    return tapped


def once(fn: Callable) -> Callable:
    """只执行一次"""
    called = [False]
    result = [None]
    
    def wrapper(*args, **kwargs):
        if not called[0]:
            called[0] = True
            result[0] = fn(*args, **kwargs)
        return result[0]
    
    return wrapper


def memoize(fn: Callable) -> Callable:
    """记忆化"""
    cache = {}
    
    def memoized(*args, **kwargs):
        key = str(args) + str(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = fn(*args, **kwargs)
        return cache[key]
    
    return memoized


def curry(fn: Callable) -> Callable:
    """柯里化"""
    arity = fn.__code__.co_argcount
    
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= arity:
            return fn(*args, **kwargs)
        return lambda *more_args, **more_kwargs: curried(*args, *more_args, **kwargs, **more_kwargs)
    
    return curried


def flip(fn: Callable) -> Callable:
    """翻转参数"""
    def flipped(*args, **kwargs):
        return fn(*reversed(args), **kwargs)
    return flipped


def time_it(fn: Callable) -> Callable:
    """计时装饰器"""
    def timed(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        print(f"{fn.__name__} took {time.time() - start:.4f}s")
        return result
    return timed


# 导出
__all__ = [
    "noop",
    "identity",
    "constant",
    "always",
    "never",
    "always_true",
    "default_to",
    "tap",
    "once",
    "memoize",
    "curry",
    "flip",
    "time_it",
]
