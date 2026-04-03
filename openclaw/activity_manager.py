"""
OpenClaw Activity Manager
====================
Inspired by Claude Code's src/utils/activityManager.ts.

活动管理器，支持：
1. 用户活动跟踪
2. CLI 活动跟踪
3. 重叠活动去重
4. 用户/CLI 时间分离统计
"""

from __future__ import annotations

import time, threading
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Set
from collections import defaultdict

# ============================================================================
# 配置
# ============================================================================

USER_ACTIVITY_TIMEOUT_MS = 5000  # 5秒

# ============================================================================
# 时间计数器
# ============================================================================

@dataclass
class TimeCounter:
    """时间计数器"""
    user_time: float = 0  # 用户活动时间（秒）
    cli_time: float = 0    # CLI 活动时间（秒）
    last_update: Optional[datetime] = None
    
    def add(self, seconds: float, type: str = "user") -> None:
        """添加时间"""
        if type == "user":
            self.user_time += seconds
        else:
            self.cli_time += seconds
        self.last_update = datetime.now(timezone(timedelta(hours=8)))
    
    @property
    def total_time(self) -> float:
        """总时间"""
        return self.user_time + self.cli_time
    
    def to_dict(self) -> dict:
        return {
            "user_time": round(self.user_time, 2),
            "cli_time": round(self.cli_time, 2),
            "total_time": round(self.total_time, 2)
        }

# ============================================================================
# 活动管理器
# ============================================================================

class ActivityManager:
    """
    活动管理器
    
    特性：
    - 用户活动和 CLI 活动分离统计
    - 自动去重重叠活动
    - 超时自动结束
    
    用法：
    ```python
    manager = ActivityManager()
    
    # 记录用户活动
    manager.record_user_activity()
    
    # 开始 CLI 活动
    manager.start_cli_activity("task-1")
    # ... 执行任务 ...
    manager.end_cli_activity("task-1")
    
    # 获取统计
    stats = manager.get_stats()
    ```
    """
    
    _instance: Optional['ActivityManager'] = None
    _lock = threading.Lock()
    
    def __init__(self, now_func=None):
        self._active_operations: Set[str] = set()
        self._last_user_activity_time: float = 0
        self._last_cli_recorded_time: float = 0
        self._is_cli_active: bool = False
        self._time_counter = TimeCounter()
        self._now = now_func or (lambda: time.time() * 1000)  # 毫秒
    
    @classmethod
    def get_instance(cls) -> 'ActivityManager':
        """获取单例"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（用于测试）"""
        with cls._lock:
            cls._instance = None
    
    @classmethod
    def create_instance(cls, now_func=None) -> 'ActivityManager':
        """创建新实例"""
        cls._instance = cls(now_func)
        return cls._instance
    
    # ============================================================================
    # 用户活动
    # ============================================================================
    
    def record_user_activity(self) -> None:
        """
        记录用户活动（用户与 CLI 交互：输入命令等）
        
        如果 CLI 正在活动，不记录用户时间
        """
        if self._is_cli_active and self._last_user_activity_time != 0:
            return
        
        now = self._now()
        
        if self._last_user_activity_time != 0:
            time_since = (now - self._last_user_activity_time) / 1000  # 转换为秒
            
            if 0 < time_since < USER_ACTIVITY_TIMEOUT_MS / 1000:
                self._time_counter.add(time_since, "user")
        
        self._last_user_activity_time = now
    
    # ============================================================================
    # CLI 活动
    # ============================================================================
    
    def start_cli_activity(self, operation_id: str) -> None:
        """
        开始 CLI 活动（工具执行、AI 响应等）
        
        Args:
            operation_id: 操作 ID（用于去重）
        """
        # 如果操作已存在，先结束它（防止重复）
        if operation_id in self._active_operations:
            self.end_cli_activity(operation_id)
        
        was_empty = len(self._active_operations) == 0
        self._active_operations.add(operation_id)
        
        if was_empty:
            self._is_cli_active = True
            self._last_cli_recorded_time = self._now()
    
    def end_cli_activity(self, operation_id: str) -> None:
        """
        结束 CLI 活动
        
        Args:
            operation_id: 操作 ID
        """
        if operation_id not in self._active_operations:
            return
        
        self._active_operations.discard(operation_id)
        
        if len(self._active_operations) == 0:
            # 记录经过的时间
            if self._is_cli_active:
                now = self._now()
                elapsed = (now - self._last_cli_recorded_time) / 1000
                if elapsed > 0:
                    self._time_counter.add(elapsed, "cli")
            
            self._is_cli_active = False
    
    def is_cli_active(self) -> bool:
        """检查 CLI 是否活动"""
        return self._is_cli_active
    
    # ============================================================================
    # 统计
    # ============================================================================
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        # 如果 CLI 还在活动，估算当前经过的时间
        user_time = self._time_counter.user_time
        cli_time = self._time_counter.cli_time
        
        if self._is_cli_active:
            now = self._now()
            elapsed = (now - self._last_cli_recorded_time) / 1000
            cli_time += elapsed
        
        return {
            "user_time_s": round(user_time, 2),
            "cli_time_s": round(cli_time, 2),
            "total_time_s": round(user_time + cli_time, 2),
            "active_operations": len(self._active_operations),
            "is_cli_active": self._is_cli_active,
            "last_user_activity_ago_s": round(
                (self._now() - self._last_user_activity_time) / 1000, 2
            ) if self._last_user_activity_time > 0 else None
        }
    
    def get_time_counter(self) -> TimeCounter:
        """获取时间计数器"""
        return self._time_counter
    
    def reset(self) -> None:
        """重置所有统计"""
        self._active_operations.clear()
        self._last_user_activity_time = 0
        self._last_cli_recorded_time = 0
        self._is_cli_active = False
        self._time_counter = TimeCounter()

# ============================================================================
# 便捷函数
# ============================================================================

def get_activity_manager() -> ActivityManager:
    """获取活动管理器单例"""
    return ActivityManager.get_instance()

def record_activity() -> None:
    """记录用户活动"""
    get_activity_manager().record_user_activity()

def start_activity(operation_id: str) -> None:
    """开始活动"""
    get_activity_manager().start_cli_activity(operation_id)

def end_activity(operation_id: str) -> None:
    """结束活动"""
    get_activity_manager().end_cli_activity(operation_id)

def get_activity_stats() -> dict:
    """获取活动统计"""
    return get_activity_manager().get_stats()
