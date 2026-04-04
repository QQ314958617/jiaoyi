"""
Log - 日志
基于 Claude Code log.ts 设计

日志工具。
"""
import logging
import sys
from datetime import datetime


# 简单日志记录器
class Logger:
    """简单日志"""
    
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    
    def __init__(self, name: str = "app", level: int = logging.INFO):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self._logger.addHandler(handler)
    
    def debug(self, msg: str):
        self._logger.debug(msg)
    
    def info(self, msg: str):
        self._logger.info(msg)
    
    def warn(self, msg: str):
        self._logger.warning(msg)
    
    def error(self, msg: str):
        self._logger.error(msg)
    
    def critical(self, msg: str):
        self._logger.critical(msg)


# 全局日志器
_default_logger = Logger()


def debug(msg: str):
    _default_logger.debug(msg)


def info(msg: str):
    _default_logger.info(msg)


def warn(msg: str):
    _default_logger.warn(msg)


def error(msg: str):
    _default_logger.error(msg)


def critical(msg: str):
    _default_logger.critical(msg)


def set_level(level: int):
    """设置日志级别"""
    _default_logger._logger.setLevel(level)


def get_logger(name: str) -> Logger:
    """获取命名日志器"""
    return Logger(name)


# 导出
__all__ = [
    "Logger",
    "debug",
    "info",
    "warn",
    "error",
    "critical",
    "set_level",
    "get_logger",
]
