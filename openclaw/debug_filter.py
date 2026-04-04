"""
DebugFilter - 调试过滤器
基于 Claude Code debug_filter.ts 设计

调试过滤器工具。
"""
import os
import re
from typing import List, Callable, Optional


class DebugFilter:
    """
    调试过滤器
    """
    
    def __init__(self):
        self._enabled = os.getenv('DEBUG', '') != ''
        self._filters: List[str] = []
        self._exclude: List[str] = []
        
        # 解析DEBUG环境变量
        debug_val = os.getenv('DEBUG', '')
        if debug_val:
            self._filters = [f.strip() for f in debug_val.split(',')]
    
    def enable(self):
        """启用调试"""
        self._enabled = True
    
    def disable(self):
        """禁用调试"""
        self._enabled = False
    
    def add_filter(self, pattern: str):
        """添加过滤器模式"""
        self._filters.append(pattern)
    
    def add_exclude(self, pattern: str):
        """添加排除模式"""
        self._exclude.append(pattern)
    
    def should_log(self, message: str, category: str = "") -> bool:
        """
        判断是否应该记录
        
        Args:
            message: 消息
            category: 类别
        """
        if not self._enabled:
            return False
        
        # 检查排除
        for pattern in self._exclude:
            if re.search(pattern, message) or re.search(pattern, category):
                return False
        
        # 如果没有过滤器，通过
        if not self._filters:
            return True
        
        # 检查匹配
        for pattern in self._filters:
            if re.search(pattern, message) or re.search(pattern, category):
                return True
        
        return False


# 全局实例
_debug_filter = DebugFilter()


def is_enabled() -> bool:
    """是否启用"""
    return _debug_filter._enabled


def enable():
    """启用"""
    _debug_filter.enable()


def disable():
    """禁用"""
    _debug_filter.disable()


def should_log(message: str, category: str = "") -> bool:
    """是否应该记录"""
    return _debug_filter.should_log(message, category)


def log(message: str, category: str = ""):
    """条件记录"""
    if should_log(message, category):
        print(f"[DEBUG:{category}] {message}")


# 导出
__all__ = [
    "DebugFilter",
    "is_enabled",
    "enable",
    "disable",
    "should_log",
    "log",
]
