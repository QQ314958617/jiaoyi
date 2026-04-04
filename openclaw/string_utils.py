"""
String Utilities - 字符串工具
基于 Claude Code stringUtils.ts 设计

提供各种字符串处理函数。
"""
import re
from typing import Optional


def escape_regex(s: str) -> str:
    """
    转义正则表达式特殊字符
    
    Args:
        s: 要转义的字符串
        
    Returns:
        转义后的字符串
    """
    return re.sub(r'[.*+?^${}()|[\]\\]', r'\\\g<0>', s)


def capitalize(s: str) -> str:
    """
    首字母大写（不转换其余字符）
    
    Args:
        s: 字符串
        
    Returns:
        首字母大写的字符串
    """
    if not s:
        return s
    return s[0].upper() + s[1:]


def plural(n: int, word: str, plural_word: Optional[str] = None) -> str:
    """
    单复数格式化
    
    Args:
        n: 数量
        word: 单数形式
        plural_word: 复数形式，默认为word+'s'
        
    Returns:
        格式化后的单词
    """
    if plural_word is None:
        plural_word = word + 's'
    return word if n == 1 else plural_word


def first_line_of(s: str) -> str:
    """
    获取第一行
    
    Args:
        s: 字符串
        
    Returns:
        第一行内容
    """
    nl = s.find('\n')
    if nl == -1:
        return s
    return s[:nl]


def count_char_in_string(s: str, char: str) -> int:
    """
    统计字符出现次数（使用indexOf优化）
    
    Args:
        s: 字符串
        char: 要统计的字符
        
    Returns:
        出现次数
    """
    count = 0
    i = s.find(char)
    while i != -1:
        count += 1
        i = s.find(char, i + 1)
    return count


def normalize_full_width_digits(s: str) -> str:
    """
    规范化全角数字为半角
    
    Args:
        s: 包含全角数字的字符串
        
    Returns:
        规范化后的字符串
    """
    # 全角数字范围：０-９ (U+FF10-U+FF19)
    return s.translate(str.maketrans(
        '０１２３４５６７８９',
        '0123456789'
    ))


def normalize_full_width_space(s: str) -> str:
    """
    规范化全角空格为半角
    
    Args:
        s: 字符串
        
    Returns:
        规范化后的字符串
    """
    # 全角空格 U+3000 -> 半角空格 U+0020
    return s.replace('\u3000', ' ')


def remove_ansi_codes(s: str) -> str:
    """
    移除ANSI转义码
    
    Args:
        s: 包含ANSI码的字符串
        
    Returns:
        纯文本字符串
    """
    # ANSI转义码模式：\x1b[...m
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_pattern.sub('', s)


def is_blank(s: Optional[str]) -> bool:
    """
    检查字符串是否为空或仅含空白
    
    Args:
        s: 字符串
        
    Returns:
        是否为空
    """
    if s is None:
        return True
    return not s.strip()


def strip_lines(s: str) -> str:
    """
    移除每行的首尾空白
    
    Args:
        s: 多行字符串
        
    Returns:
        处理后的字符串
    """
    return '\n'.join(line.strip() for line in s.splitlines())


def lines(s: str) -> int:
    """
    计算行数
    
    Args:
        s: 字符串
        
    Returns:
        行数
    """
    if not s:
        return 0
    return s.count('\n') + (1 if not s.endswith('\n') else 0)


def words(s: str) -> int:
    """
    计算单词数
    
    Args:
        s: 字符串
        
    Returns:
        单词数
    """
    if not s or not s.strip():
        return 0
    return len(re.findall(r'\S+', s))


# 导出
__all__ = [
    "escape_regex",
    "capitalize",
    "plural",
    "first_line_of",
    "count_char_in_string",
    "normalize_full_width_digits",
    "normalize_full_width_space",
    "remove_ansi_codes",
    "is_blank",
    "strip_lines",
    "lines",
    "words",
]
