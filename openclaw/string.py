"""
String - 字符串工具
基于 Claude Code string.ts 设计

字符串处理工具。
"""
import re
from typing import List, Optional


def capitalize(text: str) -> str:
    """首字母大写"""
    return text.capitalize()


def upper(text: str) -> str:
    """转大写"""
    return text.upper()


def lower(text: str) -> str:
    """转小写"""
    return text.lower()


def title(text: str) -> str:
    """标题格式"""
    return text.title()


def snake_case(text: str) -> str:
    """转蛇形格式"""
    # 插入下划线在大写字母前
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def camel_case(text: str) -> str:
    """转驼峰格式"""
    parts = text.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def pascal_case(text: str) -> str:
    """转帕斯卡格式"""
    parts = text.split('_')
    return ''.join(p.capitalize() for p in parts)


def kebab_case(text: str) -> str:
    """转短横线格式"""
    return snake_case(text).replace('_', '-')


def trim(text: str) -> str:
    """去除首尾空白"""
    return text.strip()


def trim_left(text: str) -> str:
    """去除左侧空白"""
    return text.lstrip()


def trim_right(text: str) -> str:
    """去除右侧空白"""
    return text.rstrip()


def pad_left(text: str, length: int, char: str = ' ') -> str:
    """左侧填充"""
    return text.ljust(length, char)


def pad_right(text: str, length: int, char: str = ' ') -> str:
    """右侧填充"""
    return text.rjust(length, char)


def truncate(text: str, length: int, suffix: str = '...') -> str:
    """截断字符串"""
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix


def reverse(text: str) -> str:
    """反转字符串"""
    return text[::-1]


def repeat(text: str, times: int) -> str:
    """重复字符串"""
    return text * times


def split(text: str, delimiter: str = None, maxsplit: int = -1) -> List[str]:
    """分割字符串"""
    if delimiter is None:
        # 按空白分割
        return text.split(maxsplit=maxsplit or None)
    return text.split(delimiter, maxsplit=maxsplit or None)


def join(items: List[str], separator: str = '') -> str:
    """连接字符串"""
    return separator.join(items)


def contains(text: str, substring: str, case_sensitive: bool = True) -> bool:
    """检查是否包含"""
    if not case_sensitive:
        text = text.lower()
        substring = substring.lower()
    return substring in text


def starts_with(text: str, prefix: str, case_sensitive: bool = True) -> bool:
    """检查开头"""
    if not case_sensitive:
        text = text.lower()
        prefix = prefix.lower()
    return text.startswith(prefix)


def ends_with(text: str, suffix: str, case_sensitive: bool = True) -> bool:
    """检查结尾"""
    if not case_sensitive:
        text = text.lower()
        suffix = suffix.lower()
    return text.endswith(suffix)


def replace(text: str, old: str, new: str, count: int = -1) -> str:
    """替换"""
    return text.replace(old, new, count if count >= 0 else None)


def replace_all(text: str, pattern: str, replacement: str) -> str:
    """正则替换"""
    return re.sub(pattern, replacement, text)


def match(text: str, pattern: str) -> Optional[str]:
    """正则匹配"""
    match = re.search(pattern, text)
    return match.group(0) if match else None


def match_all(text: str, pattern: str) -> List[str]:
    """正则匹配所有"""
    return re.findall(pattern, text)


def is_empty(text: str) -> bool:
    """是否为空或空白"""
    return not text or text.strip() == ''


def is_numeric(text: str) -> bool:
    """是否为数字"""
    return text.isdigit()


def is_alpha(text: str) -> bool:
    """是否为字母"""
    return text.isalpha()


def is_alphanumeric(text: str) -> bool:
    """是否为字母或数字"""
    return text.isalnum()


def word_count(text: str) -> int:
    """词数"""
    return len(text.split())


def char_count(text: str) -> int:
    """字符数"""
    return len(text)


# 导出
__all__ = [
    "capitalize",
    "upper",
    "lower",
    "title",
    "snake_case",
    "camel_case",
    "pascal_case",
    "kebab_case",
    "trim",
    "trim_left",
    "trim_right",
    "pad_left",
    "pad_right",
    "truncate",
    "reverse",
    "repeat",
    "split",
    "join",
    "contains",
    "starts_with",
    "ends_with",
    "replace",
    "replace_all",
    "match",
    "match_all",
    "is_empty",
    "is_numeric",
    "is_alpha",
    "is_alphanumeric",
    "word_count",
    "char_count",
]
