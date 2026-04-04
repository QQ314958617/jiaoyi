"""
Date - 日期
基于 Claude Code date.ts 设计

日期工具。
"""
from datetime import datetime, date


def today() -> date:
    """今天的日期"""
    return date.today()


def tomorrow() -> date:
    """明天的日期"""
    from datetime import timedelta
    return date.today() + timedelta(days=1)


def yesterday() -> date:
    """昨天的日期"""
    from datetime import timedelta
    return date.today() - timedelta(days=1)


def is_today(d: date) -> bool:
    """是否今天"""
    return d == date.today()


def is_past(d: date) -> bool:
    """是否过去"""
    return d < date.today()


def is_future(d: date) -> bool:
    """是否未来"""
    return d > date.today()


def days_between(d1: date, d2: date) -> int:
    """两日期间天数"""
    return abs((d2 - d1).days)


def add_days(d: date, days: int) -> date:
    """加天数"""
    from datetime import timedelta
    return d + timedelta(days=days)


def format_date(d: date, fmt: str = "%Y-%m-%d") -> str:
    """格式化日期"""
    return d.strftime(fmt)


def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> date:
    """解析日期字符串"""
    return datetime.strptime(date_str, fmt).date()


# 导出
__all__ = [
    "today",
    "tomorrow",
    "yesterday",
    "is_today",
    "is_past",
    "is_future",
    "days_between",
    "add_days",
    "format_date",
    "parse_date",
]
