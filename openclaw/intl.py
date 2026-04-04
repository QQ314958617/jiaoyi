"""
Intl - 国际化工具
基于 Claude Code intl.ts 设计

Unicode文本处理和格式化。
"""
from functools import lru_cache
from typing import Optional
import re


# 简单的Unicode分段器（Python原生实现）
def first_grapheme(text: str) -> str:
    """
    获取第一个字素簇
    
    Args:
        text: 文本
        
    Returns:
        第一个字素
    """
    if not text:
        return ''
    
    # 简单的字素边界检测
    # 对于大多数用例，这足够处理Emoji和组合字符
    chars = list(text)
    
    # 处理Emoji ZWJ序列
    zwj = '\u200d'  # Zero Width Joiner
    i = 0
    while i < len(chars):
        c = chars[i]
        result = c
        
        # 检查是否跟随组合字符
        j = i + 1
        while j < len(chars):
            next_c = chars[j]
            # 组合字符
            if _is_combining_char(next_c):
                result += next_c
                j += 1
            # ZWJ序列
            elif next_c == zwj and j + 1 < len(chars):
                result += next_c + chars[j + 1]
                j += 2
            else:
                break
        
        return result
    
    return chars[0] if chars else ''


def last_grapheme(text: str) -> str:
    """
    获取最后一个字素簇
    
    Args:
        text: 文本
        
    Returns:
        最后一个字素
    """
    if not text:
        return ''
    
    chars = list(text)
    zwj = '\u200d'
    i = len(chars) - 1
    result = chars[i]
    
    # 向后检查组合字符
    while i > 0:
        prev_idx = i - 1
        prev_c = chars[prev_idx]
        
        if _is_combining_char(prev_c) or prev_c == zwj:
            result = prev_c + result
            i = prev_idx
        else:
            break
    
    return result


def _is_combining_char(c: str) -> bool:
    """检查是否为组合字符"""
    code = ord(c)
    # 组合用区分标记
    return (
        0x0300 <= code <= 0x036F or  # Combining Diacritical Marks
        0x1AB0 <= code <= 0x1AFF or  # Combining Diacritical Marks Extended
        0x1DC0 <= code <= 0x1DFF or  # Combining Diacritical Marks Supplement
        0x20D0 <= code <= 0x20FF or  # Combining Diacritical Marks for Symbols
        0xFE20 <= code <= 0xFE2F  # Combining Half Marks
    )


@lru_cache(maxsize=1)
def get_timezone() -> str:
    """
    获取时区
    
    Returns:
        时区名称
    """
    import time
    return time.tzname[0] or 'UTC'


@lru_cache(maxsize=1)
def get_system_locale_language() -> Optional[str]:
    """
    获取系统语言
    
    Returns:
        语言代码
    """
    import locale
    try:
        lang = locale.getdefaultlocale()[0]
        if lang:
            return lang.split('_')[0]
    except Exception:
        pass
    return 'en'


def get_relative_time_format(
    style: str = 'long',
    numeric: str = 'always',
) -> callable:
    """
    获取相对时间格式化器
    
    Args:
        style: 样式
        numeric: 数字格式
        
    Returns:
        格式化函数
    """
    def format(value: int, unit: str) -> str:
        # 简化实现
        if unit == 'day':
            if value == 1:
                return 'tomorrow' if value > 0 else 'yesterday'
            return f'{abs(value)} days'
        elif unit == 'hour':
            return f'{abs(value)} hours'
        elif unit == 'minute':
            return f'{abs(value)} minutes'
        elif unit == 'second':
            return f'{abs(value)} seconds'
        return f'{value} {unit}s'
    
    return format


# 导出
__all__ = [
    "first_grapheme",
    "last_grapheme",
    "get_timezone",
    "get_system_locale_language",
    "get_relative_time_format",
]
