"""
Debug - 调试日志工具
基于 Claude Code debug.ts 设计

提供分级调试日志功能。
"""
import os
import sys
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .env_utils import is_env_truthy


class DebugLevel(Enum):
    """调试级别"""
    VERBOSE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


# 级别名称映射
LEVEL_NAMES = {
    'verbose': DebugLevel.VERBOSE,
    'debug': DebugLevel.DEBUG,
    'info': DebugLevel.INFO,
    'warn': DebugLevel.WARN,
    'error': DebugLevel.ERROR,
}


def get_min_debug_level() -> DebugLevel:
    """
    获取最小调试级别
    
    从环境变量CLAUDE_CODE_DEBUG_LOG_LEVEL读取。
    
    Returns:
        最小调试级别
    """
    raw = os.environ.get('CLAUDE_CODE_DEBUG_LOG_LEVEL', '').lower().strip()
    if raw in LEVEL_NAMES:
        return LEVEL_NAMES[raw]
    return DebugLevel.DEBUG


def is_debug_mode() -> bool:
    """
    检查是否启用调试模式
    
    Returns:
        是否启用
    """
    return (
        is_env_truthy(os.environ.get('DEBUG')) or
        is_env_truthy(os.environ.get('DEBUG_SDK')) or
        '--debug' in sys.argv or
        '-d' in sys.argv or
        any(arg.startswith('--debug=') for arg in sys.argv)
    )


def is_debug_to_stderr() -> bool:
    """
    检查是否输出到stderr
    
    Returns:
        是否输出到stderr
    """
    return is_env_truthy(os.environ.get('DEBUG__TO_STDERR'))


def is_debug_to_file() -> bool:
    """
    检查是否输出到文件
    
    Returns:
        是否输出到文件
    """
    return bool(os.environ.get('DEBUG_FILE'))


def get_debug_file_path() -> Optional[str]:
    """
    获取调试日志文件路径
    
    Returns:
        文件路径或None
    """
    return os.environ.get('DEBUG_FILE')


# 调试消息过滤器
_debug_filter: Optional[callable] = None


def set_debug_filter(filter_fn: Optional[callable]) -> None:
    """
    设置调试过滤器
    
    Args:
        filter_fn: 过滤器函数
    """
    global _debug_filter
    _debug_filter = filter_fn


def should_show_debug_message(message: str, level: DebugLevel = DebugLevel.DEBUG) -> bool:
    """
    检查是否应显示调试消息
    
    Args:
        message: 消息内容
        level: 消息级别
        
    Returns:
        是否应显示
    """
    # 检查级别
    if level.value < get_min_debug_level().value:
        return False
    
    # 检查过滤器
    if _debug_filter:
        return _debug_filter(message)
    
    return True


@dataclass
class DebugEntry:
    """调试日志条目"""
    level: DebugLevel
    message: str
    timestamp: float
    formatted: str


class DebugLogger:
    """
    调试日志记录器
    
    支持分级日志和多种输出目标。
    """
    
    _instance: Optional["DebugLogger"] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._entries: List[DebugEntry] = []
        self._max_entries = 1000
        self._file_handle: Optional[object] = None
    
    @classmethod
    def get_instance(cls) -> "DebugLogger":
        """获取单例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def log(
        self,
        message: str,
        level: DebugLevel = DebugLevel.DEBUG,
    ) -> None:
        """
        记录调试消息
        
        Args:
            message: 消息
            level: 级别
        """
        if not is_debug_mode():
            return
        
        if not should_show_debug_message(message, level):
            return
        
        timestamp = time.time()
        formatted = self._format_entry(level, timestamp, message)
        
        entry = DebugEntry(
            level=level,
            message=message,
            timestamp=timestamp,
            formatted=formatted,
        )
        
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max_entries:
                self._entries.pop(0)
        
        # 输出到stderr
        if is_debug_to_stderr():
            print(formatted, file=sys.stderr)
        
        # 输出到文件
        if is_debug_to_file():
            self._write_to_file(formatted)
    
    def _format_entry(
        self,
        level: DebugLevel,
        timestamp: float,
        message: str,
    ) -> str:
        """格式化日志条目"""
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        level_name = level.name.upper()
        return f"[{dt.isoformat()}] {level_name}: {message}"
    
    def _write_to_file(self, message: str) -> None:
        """写入文件"""
        if not is_debug_to_file():
            return
        
        path = get_debug_file_path()
        if not path:
            return
        
        try:
            if self._file_handle is None:
                self._file_handle = open(path, 'a')
            self._file_handle.write(message + '\n')
            self._file_handle.flush()
        except Exception:
            pass
    
    def close(self) -> None:
        """关闭日志"""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
    
    def get_entries(self) -> List[DebugEntry]:
        """获取所有条目"""
        with self._lock:
            return list(self._entries)
    
    def clear(self) -> None:
        """清空条目"""
        with self._lock:
            self._entries.clear()


# 便捷函数
def log_verbose(message: str) -> None:
    """记录VERBOSE级别消息"""
    DebugLogger.get_instance().log(message, DebugLevel.VERBOSE)


def log_debug(message: str) -> None:
    """记录DEBUG级别消息"""
    DebugLogger.get_instance().log(message, DebugLevel.DEBUG)


def log_info(message: str) -> None:
    """记录INFO级别消息"""
    DebugLogger.get_instance().log(message, DebugLevel.INFO)


def log_warn(message: str) -> None:
    """记录WARN级别消息"""
    DebugLogger.get_instance().log(message, DebugLevel.WARN)


def log_error(message: str) -> None:
    """记录ERROR级别消息"""
    DebugLogger.get_instance().log(message, DebugLevel.ERROR)


def log_for_debugging(message: str) -> None:
    """记录调试消息（兼容别名）"""
    log_debug(message)


# 导出
__all__ = [
    "DebugLevel",
    "DebugEntry",
    "DebugLogger",
    "get_min_debug_level",
    "is_debug_mode",
    "is_debug_to_stderr",
    "is_debug_to_file",
    "get_debug_file_path",
    "set_debug_filter",
    "should_show_debug_message",
    "log_verbose",
    "log_debug",
    "log_info",
    "log_warn",
    "log_error",
    "log_for_debugging",
]
