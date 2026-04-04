"""
Format - 格式化
基于 Claude Code format.ts 设计

格式化工具。
"""
from typing import Any


def format_size(bytes: int) -> str:
    """
    格式化字节大小
    
    Args:
        bytes: 字节数
        
    Returns:
        格式化字符串 (如 "1.5 MB")
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    size = float(bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    
    return f"{size:.2f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """
    格式化时长
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化字符串 (如 "1h 30m")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {seconds:.0f}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    if hours < 24:
        return f"{hours}h {minutes}m"
    
    days = hours // 24
    hours = hours % 24
    
    return f"{days}d {hours}h"


def format_number(num: float, decimals: int = 2) -> str:
    """
    格式化数字
    
    Args:
        num: 数字
        decimals: 小数位数
        
    Returns:
        格式化字符串
    """
    return f"{num:,.{decimals}f}"


def format_percent(value: float, decimals: int = 1) -> str:
    """
    格式化百分比
    
    Args:
        value: 值 (0-1 或 0-100)
        decimals: 小数位数
        
    Returns:
        百分比字符串
    """
    if value <= 1:
        value *= 100
    return f"{value:.{decimals}f}%"


def format_currency(
    amount: float,
    symbol: str = '¥',
    decimals: int = 2,
) -> str:
    """
    格式化货币
    
    Args:
        amount: 金额
        symbol: 货币符号
        decimals: 小数位数
        
    Returns:
        货币字符串
    """
    return f"{symbol}{amount:,.{decimals}f}"


def format_date(date_obj, fmt: str = '%Y-%m-%d') -> str:
    """
    格式化日期
    
    Args:
        date_obj: 日期对象
        fmt: 格式字符串
        
    Returns:
        格式化字符串
    """
    return date_obj.strftime(fmt)


def format_list(items: list, separator: str = ', ', last_separator: str = ' and ') -> str:
    """
    格式化列表为可读字符串
    
    Args:
        items: 项目列表
        separator: 分隔符
        last_separator: 最后一个分隔符
        
    Returns:
        格式化字符串
    """
    if not items:
        return ''
    
    if len(items) == 1:
        return str(items[0])
    
    if len(items) == 2:
        return f"{items[0]}{last_separator}{items[1]}"
    
    return separator.join(str(item) for item in items[:-1]) + last_separator + str(items[-1])


def format_phone(phone: str) -> str:
    """
    格式化手机号
    
    Args:
        phone: 手机号
        
    Returns:
        格式化字符串 (如 "138-1234-5678")
    """
    digits = ''.join(c for c in phone if c.isdigit())
    
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    
    return phone


def truncate(text: str, length: int, suffix: str = '...') -> str:
    """
    截断文本
    
    Args:
        text: 文本
        length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的字符串
    """
    if len(text) <= length:
        return text
    
    return text[:length - len(suffix)] + suffix


def camel_to_snake(text: str) -> str:
    """驼峰转蛇形"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def snake_to_camel(text: str) -> str:
    """蛇形转驼峰"""
    components = text.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


# 导出
__all__ = [
    "format_size",
    "format_duration",
    "format_number",
    "format_percent",
    "format_currency",
    "format_date",
    "format_list",
    "format_phone",
    "truncate",
    "camel_to_snake",
    "snake_to_camel",
]
