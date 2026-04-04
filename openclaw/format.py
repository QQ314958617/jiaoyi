"""
Format Utilities - 格式化工具
基于 Claude Code format.ts 设计

提供各种格式化函数：文件大小、时长、日期等。
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


def format_file_size(size_in_bytes: int) -> str:
    """
    格式化文件大小为人类可读字符串
    
    Args:
        size_in_bytes: 字节数
        
    Returns:
        格式化后的大小字符串 (e.g., "1.5KB", "2.3MB")
    """
    if size_in_bytes < 1024:
        return f"{size_in_bytes} bytes"
    
    kb = size_in_bytes / 1024
    if kb < 1024:
        result = f"{kb:.1f}KB"
        return result.rstrip('0').rstrip('.')
    
    mb = kb / 1024
    if mb < 1024:
        result = f"{mb:.1f}MB"
        return result.rstrip('0').rstrip('.')
    
    gb = mb / 1024
    result = f"{gb:.1f}GB"
    return result.rstrip('0').rstrip('.')


def format_seconds_short(ms: float) -> str:
    """
    格式化毫秒为秒（保留1位小数）
    
    Args:
        ms: 毫秒数
        
    Returns:
        格式化后的秒数字符串 (e.g., "1.2s")
    """
    return f"{(ms / 1000):.1f}s"


def format_duration(
    ms: float,
    hide_trailing_zeros: bool = False,
    most_significant_only: bool = False,
) -> str:
    """
    格式化时长
    
    Args:
        ms: 毫秒数
        hide_trailing_zeros: 隐藏尾部0
        most_significant_only: 只显示最高单位
        
    Returns:
        格式化后的时长字符串 (e.g., "1h 30m", "2d")
    """
    if ms < 60000:  # < 1分钟
        if ms == 0:
            return "0s"
        if ms < 1:
            return f"{(ms / 1000):.1f}s"
        return f"{int(ms // 1000)}s"
    
    # 计算各单元
    days = int(ms // 86400000)
    hours = int((ms % 86400000) // 3600000)
    minutes = int((ms % 3600000) // 60000)
    seconds = round((ms % 60000) / 1000)
    
    # 处理进位
    if seconds == 60:
        seconds = 0
        minutes += 1
    if minutes == 60:
        minutes = 0
        hours += 1
    if hours == 24:
        hours = 0
        days += 1
    
    # 只显示最高单位
    if most_significant_only:
        if days > 0:
            return f"{days}d"
        if hours > 0:
            return f"{hours}h"
        if minutes > 0:
            return f"{minutes}m"
        return f"{seconds}s"
    
    # 构建完整格式
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)


def format_relative_time(
    timestamp: float | datetime,
    timezone_str: str = "UTC",
) -> str:
    """
    格式化相对时间
    
    Args:
        timestamp: Unix时间戳或datetime对象
        timezone_str: 时区
        
    Returns:
        相对时间字符串 (e.g., "2 hours ago", "in 3 days")
    """
    if isinstance(timestamp, (int, float)):
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    else:
        dt = timestamp
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 0:
        # 未来时间
        seconds = -seconds
        if seconds < 60:
            return "in a moment"
        if seconds < 3600:
            mins = int(seconds / 60)
            return f"in {mins} minute{'s' if mins != 1 else ''}"
        if seconds < 86400:
            hours = int(seconds / 3600)
            return f"in {hours} hour{'s' if hours != 1 else ''}"
        days = int(seconds / 86400)
        return f"in {days} day{'s' if days != 1 else ''}"
    else:
        # 过去时间
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            mins = int(seconds / 60)
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        if seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        days = int(seconds / 86400)
        if days == 1:
            return "yesterday"
        if days < 30:
            return f"{days} days ago"
        if days < 365:
            months = int(days / 30)
            return f"{months} month{'s' if months != 1 else ''} ago"
        years = int(days / 365)
        return f"{years} year{'s' if years != 1 else ''} ago"


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        s: 要截断的字符串
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


# 导出
__all__ = [
    "format_file_size",
    "format_seconds_short",
    "format_duration",
    "format_relative_time",
    "truncate_string",
]
