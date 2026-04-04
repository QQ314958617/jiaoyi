"""
Flow - 流程控制
基于 Claude Code flow.ts 设计

流程控制工具。
"""
from typing import Any, Callable, List, TypeVar

T = TypeVar('T')


def pipe(*funcs: Callable) -> Callable:
    """
    管道函数
    
    pipe(f, g, h)(x) = h(g(f(x)))
    
    Args:
        *funcs: 函数列表
        
    Returns:
        管道函数
    """
    def piped(x):
        result = x
        for func in funcs:
            result = func(result)
        return result
    return piped


def compose(*funcs: Callable) -> Callable:
    """
    函数组合
    
    compose(f, g, h)(x) = f(g(h(x)))
    
    Args:
        *funcs: 函数列表
        
    Returns:
        组合函数
    """
    def composed(x):
        result = x
        for func in reversed(funcs):
            result = func(result)
        return result
    return composed


def branch(
    condition: Callable,
    if_true: Callable,
    if_false: Callable,
) -> Callable:
    """
    条件分支
    
    Args:
        condition: 条件函数
        if_true: 条件为真时执行
        if_false: 条件为假时执行
        
    Returns:
        执行后的函数
    """
    def branched(x):
        if condition(x):
            return if_true(x)
        return if_false(x)
    return branched


def switch(
    value: Any,
    cases: dict,
    default: Callable = None,
) -> Any:
    """
    switch语句
    
    Args:
        value: 值
        cases: {value: result} 映射
        default: 默认处理
        
    Returns:
        case结果
    """
    if value in cases:
        result = cases[value]
        if callable(result):
            return result()
        return result
    
    if default:
        return default()
    
    return None


def try_catch(
    try_fn: Callable,
    catch_fn: Callable[[Exception], Any] = None,
    finally_fn: Callable = None,
) -> Any:
    """
    try-catch-finally
    
    Args:
        try_fn: try块
        catch_fn: catch块
        finally_fn: finally块
        
    Returns:
        try或catch结果
    """
    try:
        return try_fn()
    except Exception as e:
        if catch_fn:
            return catch_fn(e)
    finally:
        if finally_fn:
            finally_fn()


def loop(
    iterable: List[T],
    body: Callable[[T, int], Any],
) -> None:
    """
    带索引的循环
    
    Args:
        iterable: 可迭代对象
        body: (item, index) -> Any
    """
    for i, item in enumerate(iterable):
        body(item, i)


def while_loop(
    condition: Callable,
    body: Callable,
    max_iterations: int = 10000,
) -> None:
    """
    条件循环
    
    Args:
        condition: 条件函数 () -> bool
        body: 循环体 () -> Any
        max_iterations: 最大迭代次数
    """
    iterations = 0
    
    while condition() and iterations < max_iterations:
        body()
        iterations += 1


def repeat(
    times: int,
    fn: Callable,
) -> List[Any]:
    """
    重复执行
    
    Args:
        times: 重复次数
        fn: 执行函数 () -> Any
        
    Returns:
        结果列表
    """
    return [fn() for _ in range(times)]


def until(
    condition: Callable,
    fn: Callable,
    max_attempts: int = 100,
) -> Any:
    """
    直到条件满足
    
    Args:
        condition: 条件函数 () -> bool
        fn: 执行函数 () -> Any
        max_attempts: 最大尝试次数
        
    Returns:
        首次满足条件时的fn结果
    """
    for _ in range(max_attempts):
        result = fn()
        if condition():
            return result
    return None


class Flow:
    """
    流程控制封装
    """
    
    def __init__(self, value: Any):
        self._value = value
    
    def pipe(self, *funcs: Callable) -> "Flow":
        """管道"""
        self._value = pipe(*funcs)(self._value)
        return self
    
    def branch(
        self,
        condition: Callable,
        if_true: Callable,
        if_false: Callable,
    ) -> "Flow":
        """分支"""
        result = branch(condition, if_true, if_false)(self._value)
        self._value = result
        return self
    
    @property
    def value(self) -> Any:
        return self._value


# 导出
__all__ = [
    "pipe",
    "compose",
    "branch",
    "switch",
    "try_catch",
    "loop",
    "while_loop",
    "repeat",
    "until",
    "Flow",
]
