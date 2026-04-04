"""
Time - 时间
基于 Claude Code time.ts 设计

时间工具。
"""
import time
from datetime import datetime, timedelta, timezone
from typing import Optional


def now_ms() -> int:
    """当前时间戳(毫秒)"""
    return int(time.time() * 1000)


def now_seconds() -> float:
    """当前时间戳(秒)"""
    return time.time()


def now_utc() -> datetime:
    """当前UTC时间"""
    return datetime.now(timezone.utc)


def now_local() -> datetime:
    """当前本地时间"""
    return datetime.now()


def from_timestamp(ts: int) -> datetime:
    """从毫秒时间戳创建"""
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc)


def to_timestamp(dt: datetime) -> int:
    """转换为毫秒时间戳"""
    return int(dt.timestamp() * 1000)


def format_time(dt: datetime = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间
    
    Args:
        dt: 日期时间(默认当前)
        fmt: 格式字符串
        
    Returns:
        格式化字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def parse_time(time_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    解析时间字符串
    
    Args:
        time_str: 时间字符串
        fmt: 格式字符串
        
    Returns:
        datetime对象
    """
    return datetime.strptime(time_str, fmt)


def add_days(dt: datetime, days: int) -> datetime:
    """加天数"""
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """加小时"""
    return dt + timedelta(hours=hours)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """加分钟"""
    return dt + timedelta(minutes=minutes)


def diff_seconds(dt1: datetime, dt2: datetime) -> float:
    """秒数差"""
    return (dt1 - dt2).total_seconds()


def is_today(dt: datetime) -> bool:
    """是否今天"""
    return dt.date() == datetime.now().date()


def start_of_day(dt: datetime) -> datetime:
    """一天开始"""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    """一天结束"""
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


class Timer:
    """
    计时器
    """
    
    def __init__(self):
        self._start: Optional[float] = None
        self._end: Optional[float] = None
    
    def start(self) -> "Timer":
        """开始"""
        self._start = time.time()
        return self
    
    def stop(self) -> float:
        """停止并返回耗时(秒)"""
        self._end = time.time()
        return self.elapsed()
    
    def elapsed(self) -> float:
        """已过时间(秒)"""
        if self._start is None:
            return 0
        end = self._end if self._end else time.time()
        return end - self._start
    
    def reset(self) -> None:
        """重置"""
        self._start = None
        self._end = None
    
    def __enter__(self) -> "Timer":
        self.start()
        return self
    
    def __exit__(self, *args) -> None:
        self.stop()


# 导出
__all__ = [
    "now_ms",
    "now_seconds",
    "now_utc",
    "now_local",
    "from_timestamp",
    "to_timestamp",
    "format_time",
    "parse_time",
    "add_days",
    "add_hours",
    "add_minutes",
    "diff_seconds",
    "is_today",
    "start_of_day",
    "end_of_day",
    "Timer",
]
