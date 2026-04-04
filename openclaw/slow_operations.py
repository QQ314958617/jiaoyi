"""
Slow Operations - 慢操作日志系统
基于 Claude Code slowOperations.ts 设计

提供慢操作检测和日志记录，用于发现性能问题。
主要功能：
- JSON.stringify/JSON.parse 包装（带慢操作检测）
- structuredClone 包装
- cloneDeep 包装
- 文件写入包装（带flush支持）
"""
import json
import time
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Union
from contextlib import contextmanager
import threading


# 慢操作阈值（毫秒）
SLOW_OPERATION_THRESHOLD_MS = 100  # 默认100ms

# 模块级重入保护
_is_logging = False


@dataclass
class SlowOperation:
    """慢操作记录"""
    description: str
    duration_ms: float
    timestamp: str = ""


# 慢操作日志列表
_slow_operations: list[SlowOperation] = []
_slow_operations_lock = threading.Lock()


def set_slow_operation_threshold(ms: Union[int, float]) -> None:
    """设置慢操作阈值"""
    global SLOW_OPERATION_THRESHOLD_MS
    SLOW_OPERATION_THRESHOLD_MS = ms


def get_slow_operations() -> list[SlowOperation]:
    """获取所有慢操作记录"""
    with _slow_operations_lock:
        return list(_slow_operations)


def clear_slow_operations() -> None:
    """清空慢操作记录"""
    with _slow_operations_lock:
        _slow_operations.clear()


def _log_slow_operation(description: str, duration_ms: float) -> None:
    """
    记录慢操作
    
    Args:
        description: 操作描述
        duration_ms: 持续时间（毫秒）
    """
    global _is_logging
    
    if duration_ms <= SLOW_OPERATION_THRESHOLD_MS:
        return
    
    if _is_logging:
        return
    
    _is_logging = True
    try:
        op = SlowOperation(
            description=description,
            duration_ms=duration_ms,
            timestamp=datetime.now().isoformat(),
        )
        
        with _slow_operations_lock:
            _slow_operations.append(op)
        
        # 打印日志
        caller_info = ""
        for line in traceback.format_stack()[:-1]:
            if 'slow_operations' not in line:
                caller_info = line.strip()
                break
        
        print(f"[SLOW OPERATION DETECTED] {description} ({duration_ms:.1f}ms){caller_info}")
        
    finally:
        _is_logging = False


class SlowOperationLogger:
    """
    慢操作日志记录器
    
    使用方式:
    ```python
    with SlowOperationLogger("JSON.stringify"):
        result = json.dumps(data)
    ```
    """
    
    def __init__(self, operation_name: str, *args: Any, **kwargs: Any):
        """
        Args:
            operation_name: 操作名称
            *args, **kwargs: 用于构建描述的参数
        """
        self.operation_name = operation_name
        self.args = args
        self.kwargs = kwargs
        self.start_time: float = 0
    
    def __enter__(self) -> "SlowOperationLogger":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        
        # 构建描述
        description = self._build_description()
        
        _log_slow_operation(description, duration_ms)
    
    def _build_description(self) -> str:
        """构建操作描述"""
        parts = [self.operation_name]
        
        def format_value(v: Any) -> str:
            if isinstance(v, list):
                return f"Array[{len(v)}]"
            elif isinstance(v, dict):
                keys = list(v.keys()) if isinstance(v, dict) else []
                return f"Object{{{len(keys)} keys}}"
            elif isinstance(v, str):
                if len(v) > 80:
                    return f'"{v[:80]}…"'
                return f'"{v}"'
            else:
                return str(v)
        
        if self.args:
            args_str = ", ".join(format_value(a) for a in self.args[:3])
            parts.append(f"({args_str})")
        
        if self.kwargs:
            kwargs_str = ", ".join(f"{k}={format_value(v)}" for k, v in list(self.kwargs.items())[:3])
            parts.append(f" {{{kwargs_str}}}")
        
        return "".join(parts)


def slow_logging(operation_name: str):
    """
    慢操作日志装饰器
    
    使用方式:
    ```python
    @slow_logging("json_dumps")
    def my_json_dumps(data):
        return json.dumps(data)
    ```
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with SlowOperationLogger(func.__name__, *args, **kwargs):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# --- 包装的操作 ---


def json_stringify(
    value: Any,
    indent: Optional[Union[int, str]] = None,
) -> str:
    """
    包装的JSON.stringify（带慢操作检测）
    
    Args:
        value: 要序列化的值
        indent: 缩进级别
        
    Returns:
        JSON字符串
    """
    with SlowOperationLogger("JSON.stringify", value):
        return json.dumps(value, indent=indent)


def json_parse(
    text: str,
    **kwargs: Any,
) -> Any:
    """
    包装的JSON.parse（带慢操作检测）
    
    Args:
        text: JSON字符串
        **kwargs: 额外参数（reviver等）
        
    Returns:
        解析后的对象
    """
    with SlowOperationLogger("JSON.parse", text):
        # 处理reviver参数
        if 'parse' in kwargs:
            reviver = kwargs.pop('parse')
            return json.loads(text, object_hook=reviver)
        return json.loads(text)


def clone_deep(value: Any) -> Any:
    """
    深拷贝（带慢操作检测）
    
    使用copy.deepcopy实现
    
    Args:
        value: 要拷贝的值
        
    Returns:
        深拷贝后的值
    """
    import copy
    with SlowOperationLogger("cloneDeep", value):
        return copy.deepcopy(value)


def clone(value: Any) -> Any:
    """
    结构化克隆（带慢操作检测）
    
    对于简单对象，使用copy.deepcopy
    复杂对象使用pickle
    
    Args:
        value: 要克隆的值
        
    Returns:
        克隆后的值
    """
    try:
        # 尝试使用结构化克隆
        import pickle
        with SlowOperationLogger("structuredClone", value):
            # 对于简单类型，直接返回
            if isinstance(value, (str, int, float, bool, type(None))):
                return value
            # 列表和字典递归处理
            if isinstance(value, list):
                return [clone(item) for item in value]
            if isinstance(value, dict):
                return {k: clone(v) for k, v in value.items()}
            # 其他类型使用pickle
            return pickle.loads(pickle.dumps(value))
    except Exception:
        # 回退到深拷贝
        return clone_deep(value)


def write_file_sync(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    flush: bool = False,
) -> None:
    """
    包装的文件写入（带慢操作检测）
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 编码
        flush: 是否强制刷新到磁盘
    """
    import os
    
    with SlowOperationLogger("fs.writeFileSync", file_path, content):
        if flush:
            # 带fsync的文件写入
            fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            try:
                os.write(fd, content.encode(encoding))
                os.fsync(fd)
            finally:
                os.close(fd)
        else:
            # 普通写入
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)


def read_file_in_range(
    file_path: str,
    offset: int = 0,
    max_lines: Optional[int] = None,
) -> dict:
    """
    按行范围读取文件
    
    Args:
        file_path: 文件路径
        offset: 起始行号（0索引）
        max_lines: 最大行数
        
    Returns:
        {
            "content": str,  # 文件内容
            "line_count": int,  # 读取的行数
            "total_lines": int,  # 文件总行数
            "truncated": bool,  # 是否被截断
        }
    """
    import os
    
    with SlowOperationLogger("fs.readFileInRange", file_path, offset, max_lines):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # 裁剪到指定范围
        if offset > 0:
            lines = lines[offset:]
        
        if max_lines is not None:
            lines = lines[:max_lines]
        
        content = ''.join(lines)
        line_count = len(lines)
        
        return {
            "content": content,
            "line_count": line_count,
            "total_lines": total_lines,
            "truncated": offset > 0 or (max_lines is not None and line_count > max_lines),
        }


# 导出
__all__ = [
    "SlowOperation",
    "SlowOperationLogger",
    "slow_logging",
    "slow_logging",
    "json_stringify",
    "json_parse",
    "clone_deep",
    "clone",
    "write_file_sync",
    "read_file_in_range",
    "SLOW_OPERATION_THRESHOLD_MS",
    "set_slow_operation_threshold",
    "get_slow_operations",
    "clear_slow_operations",
]
