"""
SessionActivity - 会话活动
基于 Claude Code session_activity.ts 设计

会话活动追踪工具。
"""
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class SessionActivity:
    """
    会话活动追踪
    """
    
    def __init__(self):
        self._activities: List[Dict] = []
        self._start_time = time.time()
    
    def record(self, action: str, metadata: dict = None):
        """
        记录活动
        
        Args:
            action: 活动类型
            metadata: 附加数据
        """
        self._activities.append({
            "action": action,
            "metadata": metadata or {},
            "timestamp": time.time(),
            "iso": datetime.now().isoformat(),
        })
    
    def actions(self) -> List[str]:
        """所有活动类型"""
        return list(set(a["action"] for a in self._activities))
    
    def by_action(self, action: str) -> List[Dict]:
        """按活动类型筛选"""
        return [a for a in self._activities if a["action"] == action]
    
    def recent(self, seconds: int = 60) -> List[Dict]:
        """最近N秒的活动"""
        cutoff = time.time() - seconds
        return [a for a in self._activities if a["timestamp"] >= cutoff]
    
    def duration(self) -> float:
        """会话时长（秒）"""
        return time.time() - self._start_time
    
    def count(self) -> int:
        """活动总数"""
        return len(self._activities)
    
    def clear(self):
        """清空"""
        self._activities = []
        self._start_time = time.time()
    
    def summary(self) -> dict:
        """汇总"""
        action_counts = {}
        for a in self._activities:
            action_counts[a["action"]] = action_counts.get(a["action"], 0) + 1
        
        return {
            "total": len(self._activities),
            "duration": self.duration(),
            "actions": action_counts,
            "start": datetime.fromtimestamp(self._start_time).isoformat(),
        }


# 全局追踪器
_activity_tracker = SessionActivity()


def get_tracker() -> SessionActivity:
    """获取全局追踪器"""
    return _activity_tracker


def record(action: str, metadata: dict = None):
    """记录活动"""
    _activity_tracker.record(action, metadata)


def recent(seconds: int = 60) -> List[Dict]:
    """最近活动"""
    return _activity_tracker.recent(seconds)


def summary() -> dict:
    """汇总"""
    return _activity_tracker.summary()


# 导出
__all__ = [
    "SessionActivity",
    "get_tracker",
    "record",
    "recent",
    "summary",
]
