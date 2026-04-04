"""
Format - 格式化
基于 Claude Code format.ts 设计

格式化工具。
"""
from typing import Any


def format_number(n: float, decimals: int = 2) -> str:
    """
    格式化数字
    
    Args:
        n: 数字
        decimals: 小数位数
        
    Returns:
        格式化字符串
    """
    return f"{n:.{decimals}f}"


def format_percent(n: float, decimals: int = 2) -> str:
    """
    格式化百分比
    
    Args:
        n: 数字（0-1）
        decimals: 小数位数
        
    Returns:
        百分比字符串
    """
    return f"{n * 100:.{decimals}f}%"


def format_currency(n: float, symbol: str = '$', decimals: int = 2) -> str:
    """
    格式化货币
    
    Args:
        n: 数字
        symbol: 货币符号
        decimals: 小数位数
        
    Returns:
        货币字符串
    """
    return f"{symbol}{n:,.{decimals}f}"


def format_bytes(bytes_count: int, decimals: int = 2) -> str:
    """
    格式化字节数
    
    Args:
        bytes_count: 字节数
        decimals: 小数位数
        
    Returns:
        格式化字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_count < 1024:
            return f"{bytes_count:.{decimals}f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.{decimals}f} PB"


def format_date(dt, fmt: str = "%Y-%m-%d") -> str:
    """
    格式化日期
    
    Args:
        dt: datetime对象
        fmt: 格式字符串
        
    Returns:
        格式化字符串
    """
    return dt.strftime(fmt)


def format_time(timestamp: float, fmt: str = "%H:%M:%S") -> str:
    """
    格式化时间
    
    Args:
        timestamp: 时间戳
        fmt: 格式字符串
        
    Returns:
        格式化字符串
    """
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime(fmt)


def format_relative(dt) -> str:
    """
    相对时间格式化
    
    Args:
        dt: datetime对象
        
    Returns:
        相对时间字符串
    """
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{int(seconds / 60)}分钟前"
    if seconds < 86400:
        return f"{int(seconds / 3600)}小时前"
    if seconds < 604800:
        return f"{int(seconds / 86400)}天前"
    return dt.strftime("%Y-%m-%d")


def pluralize(word: str, count: int, plural: str = None) -> str:
    """
    复数化
    
    Args:
        word: 单数形式
        count: 数量
        plural: 复数形式（默认加s）
        
    Returns:
        复数字符串
    """
    if count == 1:
        return word
    return plural or f"{word}s"


def truncate_words(text: str, length: int, suffix: str = '...') -> str:
    """
    按单词截断
    
    Args:
        text: 文本
        length: 最大单词数
        suffix: 后缀
        
    Returns:
        截断后的文本
    """
    words = text.split()
    if len(words) <= length:
        return text
    return ' '.join(words[:length]) + suffix


# 导出
__all__ = [
    "format_number",
    "format_percent",
    "format_currency",
    "format_bytes",
    "format_date",
    "format_time",
    "format_relative",
    "pluralize",
    "truncate_words",
]
