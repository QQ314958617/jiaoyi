"""
Debug - 调试工具
基于 Claude Code debug.ts 设计

调试工具。
"""
import sys
import time
from functools import wraps
from typing import Any, Callable


DEBUG = False


def enable_debug() -> None:
    """启用调试模式"""
    global DEBUG
    DEBUG = True


def disable_debug() -> None:
    """禁用调试模式"""
    global DEBUG
    DEBUG = False


def is_debug() -> bool:
    """是否为调试模式"""
    return DEBUG


def debug(*args, **kwargs) -> None:
    """调试输出"""
    if DEBUG:
        print("[DEBUG]", *args, **kwargs)


def debug_call(func: Callable) -> Callable:
    """
    调试函数调用
    
    打印函数名和参数。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if DEBUG:
            print(f"[CALL] {func.__name__}({args}, {kwargs})")
        
        start = time.time()
        try:
            result = func(*args, **kwargs)
            if DEBUG:
                elapsed = time.time() - start
                print(f"[RETURN] {func.__name__} -> {result} ({elapsed:.3f}s)")
            return result
        except Exception as e:
            if DEBUG:
                elapsed = time.time() - start
                print(f"[ERROR] {func.__name__} -> {e} ({elapsed:.3f}s)")
            raise
    
    return wrapper


def debug_async(func: Callable) -> Callable:
    """异步版本debug_call"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if DEBUG:
            print(f"[CALL] {func.__name__}({args}, {kwargs})")
        
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            if DEBUG:
                elapsed = time.time() - start
                print(f"[RETURN] {func.__name__} -> {result} ({elapsed:.3f}s)")
            return result
        except Exception as e:
            if DEBUG:
                elapsed = time.time() - start
                print(f"[ERROR] {func.__name__} -> {e} ({elapsed:.3f}s)")
            raise
    
    return wrapper


def inspect(value: Any, name: str = None) -> Any:
    """
    检查值
    
    调试时打印并返回值。
    """
    if DEBUG:
        if name:
            print(f"[INSPECT] {name} = {value}")
        else:
            print(f"[INSPECT] {value}")
    return value


def breakpoint() -> None:
    """断点"""
    if DEBUG:
        import pdb
        pdb.set_trace()


def log_value(label: str, value: Any) -> None:
    """记录值"""
    if DEBUG:
        print(f"[LOG] {label}: {value}")


class DebugContext:
    """
    调试上下文
    """
    
    def __init__(self, name: str):
        self.name = name
        self.start = None
    
    def __enter__(self):
        self.start = time.time()
        if DEBUG:
            print(f"[ENTER] {self.name}")
        return self
    
    def __exit__(self, *args):
        elapsed = time.time() - self.start
        if DEBUG:
            print(f"[EXIT] {self.name} ({elapsed:.3f}s)")


def dump(obj: Any, name: str = None) -> None:
    """导出对象信息"""
    if DEBUG:
        if name:
            print(f"[DUMP] {name}:")
        for attr in dir(obj):
            if not attr.startswith('_'):
                print(f"  {attr} = {getattr(obj, attr)}")


# 导出
__all__ = [
    "DEBUG",
    "enable_debug",
    "disable_debug",
    "is_debug",
    "debug",
    "debug_call",
    "debug_async",
    "inspect",
    "breakpoint",
    "log_value",
    "DebugContext",
    "dump",
]
