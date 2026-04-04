"""
Activity Manager - 活动管理器
基于 Claude Code activityManager.ts 设计

跟踪用户和CLI的活动状态。
"""
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ActiveTimeEntry:
    """活动时间条目"""
    duration: float
    entry_type: str  # "user" or "cli"
    timestamp: float


class ActiveTimeCounter:
    """活动时间计数器"""
    
    def __init__(self):
        self._entries: list[ActiveTimeEntry] = []
        self._lock = threading.Lock()
    
    def add(self, duration: float, entry_type: str = "user") -> None:
        """
        添加时间条目
        
        Args:
            duration: 持续时间（秒）
            entry_type: 类型 ("user" 或 "cli")
        """
        with self._lock:
            self._entries.append(ActiveTimeEntry(
                duration=duration,
                entry_type=entry_type,
                timestamp=time.time(),
            ))
    
    def get_total(self, entry_type: Optional[str] = None) -> float:
        """
        获取总时间
        
        Args:
            entry_type: 可选的类型过滤
            
        Returns:
            总时间（秒）
        """
        with self._lock:
            if entry_type:
                return sum(
                    e.duration for e in self._entries
                    if e.entry_type == entry_type
                )
            return sum(e.duration for e in self._entries)
    
    def get_entries(self) -> list[ActiveTimeEntry]:
        """获取所有条目"""
        with self._lock:
            return list(self._entries)
    
    def clear(self) -> None:
        """清空计数器"""
        with self._lock:
            self._entries.clear()


class ActivityManager:
    """
    活动管理器
    
    跟踪用户和CLI的活动，自动去重重叠操作。
    """
    
    # 用户活动超时（5秒）
    USER_ACTIVITY_TIMEOUT_MS = 5000
    
    _instance: Optional["ActivityManager"] = None
    
    def __init__(
        self,
        get_now: Optional[Callable[[], float]] = None,
    ):
        self._get_now = get_now or (lambda: time.time() * 1000)
        self._active_operations: set = set()
        self._last_user_activity_time: float = 0
        self._last_cli_recorded_time: float = self._get_now()
        self._is_cli_active: bool = False
        self._active_time_counter = ActiveTimeCounter()
    
    @classmethod
    def get_instance(cls) -> "ActivityManager":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """重置单例（测试用）"""
        cls._instance = None
    
    @classmethod
    def create_instance(
        cls,
        get_now: Optional[Callable[[], float]] = None,
    ) -> "ActivityManager":
        """创建新实例（测试用）"""
        cls._instance = cls(get_now)
        return cls._instance
    
    def record_user_activity(self) -> None:
        """记录用户活动"""
        if not self._is_cli_active and self._last_user_activity_time != 0:
            now = self._get_now()
            time_since = (now - self._last_user_activity_time) / 1000  # 转为秒
            
            if time_since > 0:
                timeout_seconds = self.USER_ACTIVITY_TIMEOUT_MS / 1000
                
                # 只在超时窗口内记录
                if time_since < timeout_seconds:
                    self._active_time_counter.add(time_since, "user")
        
        # 更新最后活动时间戳
        self._last_user_activity_time = self._get_now()
    
    def record_cli_activity(self) -> None:
        """记录CLI活动"""
        now = self._get_now()
        
        # 记录CLI未激活期间的用户时间
        if not self._is_cli_active and self._last_user_activity_time != 0:
            time_since = (now - self._last_user_activity_time) / 1000
            if time_since > 0:
                timeout_seconds = self.USER_ACTIVITY_TIMEOUT_MS / 1000
                if time_since < timeout_seconds:
                    self._active_time_counter.add(time_since, "user")
        
        self._is_cli_active = True
        self._last_user_activity_time = 0  # 重置用户活动时间
    
    def end_cli_activity(self) -> None:
        """结束CLI活动"""
        if self._is_cli_active:
            now = self._get_now()
            time_since = (now - self._last_cli_recorded_time) / 1000
            
            if time_since > 0:
                self._active_time_counter.add(time_since, "cli")
            
            self._last_cli_recorded_time = now
            self._is_cli_active = False
    
    def start_operation(self, operation: str) -> None:
        """
        开始操作
        
        Args:
            operation: 操作名称
        """
        self._active_operations.add(operation)
    
    def end_operation(self, operation: str) -> None:
        """
        结束操作
        
        Args:
            operation: 操作名称
        """
        self._active_operations.discard(operation)
    
    def is_operation_active(self, operation: str) -> bool:
        """
        检查操作是否活跃
        
        Args:
            operation: 操作名称
            
        Returns:
            是否活跃
        """
        return operation in self._active_operations
    
    def get_active_operations(self) -> set:
        """获取所有活跃操作"""
        return set(self._active_operations)
    
    def get_active_time_counter(self) -> ActiveTimeCounter:
        """获取活动时间计数器"""
        return self._active_time_counter
    
    def get_user_active_time(self) -> float:
        """获取用户活动时间（秒）"""
        return self._active_time_counter.get_total("user")
    
    def get_cli_active_time(self) -> float:
        """获取CLI活动时间（秒）"""
        return self._active_time_counter.get_total("cli")


# 全局实例访问
_activity_manager: Optional[ActivityManager] = None


def get_activity_manager() -> ActivityManager:
    """获取全局活动管理器"""
    global _activity_manager
    if _activity_manager is None:
        _activity_manager = ActivityManager.get_instance()
    return _activity_manager


# 导出
__all__ = [
    "ActivityManager",
    "ActiveTimeCounter",
    "ActiveTimeEntry",
    "get_activity_manager",
]
