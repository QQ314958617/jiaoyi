"""
String - 字符串
基于 Claude Code string.ts 设计

字符串工具。
"""
import re
from typing import List


def capitalize(text: str) -> str:
    """首字母大写"""
    return text.capitalize()


def upper_first(text: str) -> str:
    """首字母大写（仅第一个）"""
    return text[0].upper() + text[1:] if text else ''


def lower_first(text: str) -> str:
    """首字母小写"""
    return text[0].lower() + text[1:] if text else ''


def camel_case(text: str) -> str:
    """驼峰命名"""
    words = re.sub(r'[-_\s]+', ' ', text).split()
    if not words:
        return ''
    return words[0].lower() + ''.join(w.capitalize() for w in words[1:])


def snake_case(text: str) -> str:
    """蛇形命名"""
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', text)
    text = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', text)
    return text.lower().replace('-', '_').replace(' ', '_')


def kebab_case(text: str) -> str:
    """短横线命名"""
    text = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1-\2', text)
    text = re.sub(r'([a-z\d])([A-Z])', r'\1-\2', text)
    return text.lower().replace('_', '-').replace(' ', '-')


def pascal_case(text: str) -> str:
    """帕斯卡命名"""
    words = re.sub(r'[-_\s]+', ' ', text).split()
    return ''.join(w.capitalize() for w in words)


def truncate(text: str, length: int, suffix: str = '...') -> str:
    """截断"""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def words(text: str) -> List[str]:
    """分词"""
    return re.findall(r'\w+', text)


def unwords(words: List[str]) -> str:
    """连接词"""
    return ' '.join(words)


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


# 导出
__all__ = [
    "capitalize",
    "upper_first",
    "lower_first",
    "camel_case",
    "snake_case",
    "kebab_case",
    "pascal_case",
    "truncate",
    "words",
    "unwords",
    "pad_start",
    "pad_end",
    "trim",
    "trim_start",
    "trim_end",
]
