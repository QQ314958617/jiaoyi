"""
Log Utilities - 日志工具
基于 Claude Code log.ts 设计

提供日志记录功能。
"""
import os
import sys
import threading
import time
from datetime import datetime, timezone
from typing import Optional

from .errors import log_error


# 内存中最近错误的数量限制
MAX_IN_MEMORY_ERRORS = 100


class InMemoryErrorLog:
    """内存错误日志"""
    
    def __init__(self, max_size: int = MAX_IN_MEMORY_ERRORS):
        self._errors: list[dict] = []
        self._max_size = max_size
        self._lock = threading.Lock()
    
    def add(self, error: str, timestamp: Optional[str] = None) -> None:
        """添加错误"""
        with self._lock:
            if len(self._errors) >= self._max_size:
                self._errors.pop(0)  # 移除最旧的
            self._errors.append({
                "error": error,
                "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            })
    
    def get_all(self) -> list[dict]:
        """获取所有错误"""
        with self._lock:
            return list(self._errors)
    
    def clear(self) -> None:
        """清空"""
        with self._lock:
            self._errors.clear()
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._errors)


# 全局实例
_in_memory_error_log: Optional[InMemoryErrorLog] = None


def get_in_memory_error_log() -> InMemoryErrorLog:
    """获取全局内存错误日志"""
    global _in_memory_error_log
    if _in_memory_error_log is None:
        _in_memory_error_log = InMemoryErrorLog()
    return _in_memory_error_log


def log_to_stderr(message: str, error: Optional[Exception] = None) -> None:
    """
    输出到stderr
    
    Args:
        message: 消息
        error: 可选的异常
    """
    if error:
        print(f"{message}: {error}", file=sys.stderr)
    else:
        print(message, file=sys.stderr)


def log_info(message: str) -> None:
    """
    记录信息日志
    
    Args:
        message: 消息
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[INFO {timestamp}] {message}", file=sys.stderr)


def log_warning(message: str) -> None:
    """
    记录警告日志
    
    Args:
        message: 消息
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[WARN {timestamp}] {message}", file=sys.stderr)


def log_debug(message: str) -> None:
    """
    记录调试日志
    
    Args:
        message: 消息
    """
    # 在调试模式下才输出
    if os.environ.get('DEBUG'):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}", file=sys.stderr)


def log_error_to_memory(error: Exception | str) -> None:
    """
    将错误记录到内存日志
    
    Args:
        error: 异常或错误字符串
    """
    error_str = str(error) if isinstance(error, Exception) else error
    get_in_memory_error_log().add(error_str)


def get_recent_errors(limit: int = 10) -> list[dict]:
    """
    获取最近的错误
    
    Args:
        limit: 返回数量限制
        
    Returns:
        错误列表
    """
    errors = get_in_memory_error_log().get_all()
    return errors[-limit:] if len(errors) > limit else errors


def date_to_filename(date: datetime) -> str:
    """
    将日期转换为文件名格式
    
    Args:
        date: 日期对象
        
    Returns:
        文件名格式的日期字符串
    """
    return date.isoformat().replace(':', '-').replace('.', '-')


def get_log_display_title(
    title: Optional[str] = None,
    summary: Optional[str] = None,
    first_prompt: Optional[str] = None,
    session_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    custom_title: Optional[str] = None,
) -> str:
    """
    获取日志显示标题
    
    优先级：agentName > customTitle > summary > firstPrompt > sessionId
    
    Args:
        title: 默认标题
        summary: 摘要
        first_prompt: 第一条提示
        session_id: 会话ID
        agent_name: Agent名称
        custom_title: 自定义标题
        
    Returns:
        显示标题
    """
    # 跳过第一提示如果是tick/goal标签（自主模式）
    if first_prompt and first_prompt.startswith('<tick>'):
        first_prompt = None
    
    # 按优先级选择
    result = (
        agent_name or
        custom_title or
        summary or
        (first_prompt[:50] + '...' if first_prompt and len(first_prompt) > 50 else first_prompt) or
        title or
        ('Autonomous session' if first_prompt and first_prompt.startswith('<tick>') else None) or
        (session_id[:8] if session_id else None) or
        ''
    )
    
    return result.strip() if result else ''


# 导出
__all__ = [
    "InMemoryErrorLog",
    "get_in_memory_error_log",
    "log_to_stderr",
    "log_info",
    "log_warning",
    "log_debug",
    "log_error_to_memory",
    "get_recent_errors",
    "date_to_filename",
    "get_log_display_title",
    "MAX_IN_MEMORY_ERRORS",
]
