"""
String2 - 字符串
基于 Claude Code string.ts 设计

字符串工具。
"""
from typing import List


def capitalize(text: str) -> str:
    """首字母大写"""
    return text.capitalize()


def upper_first(text: str) -> str:
    """首字母大写"""
    return text[0].upper() + text[1:] if text else ''


def lower_first(text: str) -> str:
    """首字母小写"""
    return text[0].lower() + text[1:] if text else ''


def camel_case(text: str) -> str:
    """驼峰命名"""
    words = text.replace('-', ' ').replace('_', ' ').split()
    if not words:
        return ''
    return words[0].lower() + ''.join(w.capitalize() for w in words[1:])


def snake_case(text: str) -> str:
    """蛇形命名"""
    result = []
    for i, char in enumerate(text):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())
    return ''.join(result).replace('-', '_')


def kebab_case(text: str) -> str:
    """短横线命名"""
    result = []
    for i, char in enumerate(text):
        if char.isupper() and i > 0:
            result.append('-')
        result.append(char.lower())
    return ''.join(result).replace('_', '-')


def kebab_case_lower(text: str) -> str:
    """全小写短横线"""
    return kebab_case(text).lower()


def pascal_case(text: str) -> str:
    """帕斯卡命名"""
    words = text.replace('-', ' ').replace('_', ' ').split()
    return ''.join(w.capitalize() for w in words)


def title_case(text: str) -> str:
    """标题大小写"""
    return text.title()


def truncate(text: str, length: int, suffix: str = '...') -> str:
    """
    截断
    
    Args:
        text: 文本
        length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def pad_start(text: str, length: int, char: str = ' ') -> str:
    """左侧填充"""
    return text.rjust(length, char)


def pad_end(text: str, length: int, char: str = ' ') -> str:
    """右侧填充"""
    return text.ljust(length, char)


def trim(text: str) -> str:
    """去除首尾空白"""
    return text.strip()


def trim_start(text: str) -> str:
    """去除左侧空白"""
    return text.lstrip()


def trim_end(text: str) -> str:
    """去除右侧空白"""
    return text.rstrip()


def words(text: str) -> List[str]:
    """分词"""
    return text.split()


def unwords(words: List[str]) -> str:
    """连接词"""
    return ' '.join(words)


# 导出
__all__ = [
    "capitalize",
    "upper_first",
    "lower_first",
    "camel_case",
    "snake_case",
    "kebab_case",
    "kebab_case_lower",
    "pascal_case",
    "title_case",
    "truncate",
    "pad_start",
    "pad_end",
    "trim",
    "trim_start",
    "trim_end",
    "words",
    "unwords",
]
