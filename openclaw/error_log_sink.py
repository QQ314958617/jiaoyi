"""
ErrorLogSink - 错误日志
基于 Claude Code error_log_sink.ts 设计

错误日志工具。
"""
import logging
import sys
import traceback
from datetime import datetime
from typing import Optional


class ErrorLogSink:
    """
    错误日志记录器
    """
    
    def __init__(self, file_path: str = None, level: int = logging.ERROR):
        """
        Args:
            file_path: 日志文件路径（可选）
            level: 记录级别
        """
        self._logger = logging.getLogger("error_sink")
        self._logger.setLevel(level)
        self._file_path = file_path
        
        # 控制台handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self._logger.addHandler(console_handler)
        
        # 文件handler
        if file_path:
            import os
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
            ))
            self._logger.addHandler(file_handler)
    
    def error(self, message: str, exc_info: Exception = None):
        """记录错误"""
        if exc_info:
            tb = ''.join(traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__))
            self._logger.error(f"{message}\n{tb}")
        else:
            self._logger.error(message)
    
    def warning(self, message: str):
        """记录警告"""
        self._logger.warning(message)
    
    def info(self, message: str):
        """记录信息"""
        self._logger.info(message)
    
    def debug(self, message: str):
        """记录调试"""
        self._logger.debug(message)


# 全局实例
_default_sink: Optional[ErrorLogSink] = None


def get_sink() -> ErrorLogSink:
    """获取全局日志实例"""
    global _default_sink
    if _default_sink is None:
        _default_sink = ErrorLogSink()
    return _default_sink


def error(message: str, exc_info: Exception = None):
    """记录错误"""
    get_sink().error(message, exc_info)


def warning(message: str):
    """记录警告"""
    get_sink().warning(message)


def info(message: str):
    """记录信息"""
    get_sink().info(message)


def log_exception(e: Exception, context: str = ""):
    """记录异常"""
    if context:
        error(f"{context}: {e}", e)
    else:
        error(str(e), e)


# 导出
__all__ = [
    "ErrorLogSink",
    "get_sink",
    "error",
    "warning",
    "info",
    "log_exception",
]
