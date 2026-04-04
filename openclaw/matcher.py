"""
Matcher - 匹配器
基于 Claude Code matcher.ts 设计

路径匹配工具。
"""
import re
from typing import List


def match(pattern: str, text: str) -> bool:
    """
    简单通配符匹配
    
    Args:
        pattern: 模式 (* 和 ?)
        text: 文本
    """
    # 转换模式为正则
    regex_pattern = ''
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == '*':
            regex_pattern += '.*'
        elif c == '?':
            regex_pattern += '.'
        elif c == '.':
            regex_pattern += r'\.'
        else:
            regex_pattern += c
        i += 1
    
    return bool(re.match(regex_pattern, text, re.IGNORECASE))


def match_many(patterns: List[str], text: str) -> bool:
    """任意模式匹配"""
    return any(match(p, text) for p in patterns)


def filter_by_pattern(items: List[str], pattern: str) -> List[str]:
    """按模式过滤"""
    return [item for item in items if match(pattern, item)]


def glob_to_regex(pattern: str) -> str:
    """
    Glob模式转正则
    
    Args:
        pattern: glob模式 (*.txt, **/*.js)
    """
    regex = ''
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == '*':
            if i + 1 < len(pattern) and pattern[i + 1] == '*':
                regex += '.*'
                i += 2
            else:
                regex += '[^/]*'
                i += 1
        elif c == '?':
            regex += '.'
        elif c == '.':
            regex += r'\.'
        else:
            regex += c
        i += 1
    
    return '^' + regex + '$'


def is_glob(text: str) -> bool:
    """是否包含glob特殊字符"""
    return '*' in text or '?' in text or '[' in text


# 导出
__all__ = [
    "match",
    "match_many",
    "filter_by_pattern",
    "glob_to_regex",
    "is_glob",
]
