"""
Duration - 持续时间
基于 Claude Code duration.ts 设计

时间持续工具。
"""
from datetime import timedelta
from typing import Union


class Duration:
    """
    持续时间
    """
    
    def __init__(self, value: float, unit: str = "seconds"):
        """
        Args:
            value: 数值
            unit: 单位 (nanoseconds/milliseconds/seconds/minutes/hours/days/weeks)
        """
        self._seconds = self._to_seconds(value, unit)
    
    def _to_seconds(self, value: float, unit: str) -> float:
        multipliers = {
            "nanoseconds": 1e-9,
            "milliseconds": 1e-3,
            "seconds": 1,
            "minutes": 60,
            "hours": 3600,
            "days": 86400,
            "weeks": 604800,
        }
        return value * multipliers.get(unit, 1)
    
    @property
    def total_nanoseconds(self) -> float:
        return self._seconds * 1e9
    
    @property
    def total_milliseconds(self) -> float:
        return self._seconds * 1e3
    
    @property
    def total_seconds(self) -> float:
        return self._seconds
    
    @property
    def total_minutes(self) -> float:
        return self._seconds / 60
    
    @property
    def total_hours(self) -> float:
        return self._seconds / 3600
    
    @property
    def total_days(self) -> float:
        return self._seconds / 86400
    
    @property
    def total_weeks(self) -> float:
        return self._seconds / 604800
    
    def __add__(self, other: "Duration") -> "Duration":
        return Duration(self._seconds + other._seconds, "seconds")
    
    def __sub__(self, other: "Duration") -> "Duration":
        return Duration(self._seconds - other._seconds, "seconds")
    
    def __mul__(self, factor: float) -> "Duration":
        return Duration(self._seconds * factor, "seconds")
    
    def __truediv__(self, other: "Duration") -> float:
        return self._seconds / other._seconds
    
    def __repr__(self) -> str:
        if self._seconds < 1:
            return f"{self.total_milliseconds:.2f}ms"
        elif self._seconds < 60:
            return f"{self._seconds:.2f}s"
        elif self._seconds < 3600:
            return f"{self.total_minutes:.2f}m"
        elif self._seconds < 86400:
            return f"{self.total_hours:.2f}h"
        else:
            return f"{self.total_days:.2f}d"
    
    def __str__(self) -> str:
        return self.__repr__()


def duration(value: float, unit: str = "seconds") -> Duration:
    """创建持续时间"""
    return Duration(value, unit)


def parse_duration(text: str) -> Duration:
    """
    解析持续时间字符串
    
    Args:
        text: 如 "1h30m", "2 days", "30s"
        
    Returns:
        Duration
    """
    import re
    
    total_seconds = 0
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*ns', 1e-9),
        (r'(\d+(?:\.\d+)?)\s*ms', 1e-3),
        (r'(\d+(?:\.\d+)?)\s*s(?:ec)?', 1),
        (r'(\d+(?:\.\d+)?)\s*m(?:in)?', 60),
        (r'(\d+(?:\.\d+)?)\s*h(?:r)?', 3600),
        (r'(\d+(?:\.\d+)?)\s*d(?:ay)?', 86400),
        (r'(\d+(?:\.\d+)?)\s*w(?:ee)?k?', 604800),
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            total_seconds += float(match.group(1)) * multiplier
    
    return Duration(total_seconds, "seconds")


# 导出
__all__ = [
    "Duration",
    "duration",
    "parse_duration",
]
