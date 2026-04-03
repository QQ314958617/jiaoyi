"""
OpenClaw Debug Utilities
====================
Inspired by Claude Code's src/utils/debug.ts.

调试工具，支持：
1. 调试模式检测
2. 调试日志分级
3. 调试文件输出
4. 性能分析
"""

from __future__ import annotations

import os, sys, time, traceback
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Optional
from functools import wraps

# ============================================================================
# 日志级别
# ============================================================================

class DebugLevel(Enum):
    VERBOSE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4

_LEVEL_ORDER = {
    "verbose": DebugLevel.VERBOSE,
    "debug": DebugLevel.DEBUG,
    "info": DebugLevel.INFO,
    "warn": DebugLevel.WARN,
    "error": DebugLevel.ERROR,
}

# ============================================================================
# 调试配置
# ============================================================================

_debug_enabled = False
_min_level = DebugLevel.DEBUG
_debug_file: Optional[str] = None
_debug_filter: Optional[str] = None

def is_debug_mode() -> bool:
    """检查是否在调试模式"""
    global _debug_enabled
    
    if _debug_enabled:
        return True
    
    # 检查环境变量
    if os.environ.get("DEBUG") in ("1", "true", "yes", "on"):
        return True
    if os.environ.get("DEBUG_SDK") in ("1", "true", "yes", "on"):
        return True
    
    # 检查命令行参数
    if "--debug" in sys.argv or "-d" in sys.argv:
        return True
    
    if any(arg.startswith("--debug=") for arg in sys.argv):
        return True
    
    return False

def enable_debug() -> None:
    """启用调试模式"""
    global _debug_enabled
    _debug_enabled = True

def set_debug_level(level: str) -> None:
    """设置调试级别"""
    global _min_level
    if level.lower() in _LEVEL_ORDER:
        _min_level = _LEVEL_ORDER[level.lower()]

def set_debug_file(path: str) -> None:
    """设置调试文件输出"""
    global _debug_file
    _debug_file = path

def set_debug_filter(pattern: str) -> None:
    """设置调试过滤器（正则表达式）"""
    global _debug_filter
    _debug_file = pattern

# ============================================================================
# 调试日志
# ============================================================================

def _should_log(level: DebugLevel) -> bool:
    """检查是否应该记录"""
    return level.value >= _min_level.value

def _format_message(level: DebugLevel, message: str, **kwargs) -> str:
    """格式化调试消息"""
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%H:%M:%S.%f")[:-3]
    prefix = level.name
    if kwargs:
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        return f"{ts} {prefix} {message} {extra}"
    return f"{ts} {prefix} {message}"

def _write_debug(level: DebugLevel, message: str, file=None, **kwargs) -> None:
    """写入调试日志"""
    if not is_debug_mode() or not _should_log(level):
        return
    
    formatted = _format_message(level, message, **kwargs)
    
    # 写入文件
    if _debug_file:
        try:
            with open(_debug_file, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except:
            pass
    
    # 写入 stderr
    print(formatted, file=sys.stderr)

# ============================================================================
# 公共接口
# ============================================================================

def debug(message: str, **kwargs) -> None:
    """记录 debug 级别日志"""
    _write_debug(DebugLevel.DEBUG, message, **kwargs)

def info(message: str, **kwargs) -> None:
    """记录 info 级别日志"""
    _write_debug(DebugLevel.INFO, message, **kwargs)

def warn(message: str, **kwargs) -> None:
    """记录 warn 级别日志"""
    _write_debug(DebugLevel.WARN, message, **kwargs)

def error(message: str, **kwargs) -> None:
    """记录 error 级别日志"""
    _write_debug(DebugLevel.ERROR, message, **kwargs)

def verbose(message: str, **kwargs) -> None:
    """记录 verbose 级别日志"""
    _write_debug(DebugLevel.VERBOSE, message, **kwargs)

# ============================================================================
# 性能分析
# ============================================================================

@dataclass
class ProfilerResult:
    name: str
    elapsed_ms: float
    start_time: float
    end_time: float

class Profiler:
    """
    性能分析器
    
    用法：
    ```python
    with Profiler("operation"):
        do_something()
    ```
    """
    
    _current: dict = {}
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = 0
        self.end_time = 0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        elapsed = (self.end_time - self.start_time) * 1000
        debug(f"[PROFILE] {self.name}: {elapsed:.2f}ms")
    
    @property
    def elapsed_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000


def profile(func: Callable) -> Callable:
    """性能分析装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            debug(f"[PROFILE] {name}: {elapsed:.2f}ms")
    return wrapper


# ============================================================================
# 断言和检查
# ============================================================================

def assert_true(condition: bool, message: str = "Assertion failed") -> None:
    """断言为真"""
    if not condition:
        raise AssertionError(message)

def assert_equal(actual: Any, expected: Any, message: str = "") -> None:
    """断言相等"""
    if actual != expected:
        msg = message or f"Expected {expected!r}, got {actual!r}"
        raise AssertionError(msg)

def assert_not_none(value: Any, message: str = "Expected not None") -> None:
    """断言不为 None"""
    if value is None:
        raise AssertionError(message)

# ============================================================================
# 堆栈跟踪
# ============================================================================

def get_stack_trace(limit: int = 10) -> str:
    """获取堆栈跟踪"""
    import traceback
    lines = traceback.format_stack()[-limit-1:-1]
    return "".join(lines)

def print_stack_trace() -> None:
    """打印堆栈跟踪"""
    traceback.print_stack()

# ============================================================================
# 调试上下文管理器
# ============================================================================

class DebugContext:
    """调试上下文（临时启用调试）"""
    
    def __init__(self, enabled: bool = True):
        self._prev = _debug_enabled
        self._enabled = enabled
    
    def __enter__(self):
        global _debug_enabled
        if self._enabled:
            _debug_enabled = True
        return self
    
    def __exit__(self, *args):
        global _debug_enabled
        _debug_enabled = self._prev
