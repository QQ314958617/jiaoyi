"""
Regex - 正则工具
基于 Claude Code regex.ts 设计

正则表达式工具。
"""
import re
from typing import List, Optional, Pattern


def compile(pattern: str, flags: int = 0) -> Pattern:
    """
    编译正则
    
    Args:
        pattern: 正则模式
        flags: 标志
        
    Returns:
        编译后的正则
    """
    return re.compile(pattern, flags)


def match(text: str, pattern: str) -> Optional[str]:
    """
    匹配一次
    
    Args:
        text: 文本
        pattern: 正则模式
        
    Returns:
        匹配的字符串或None
    """
    m = re.search(pattern, text)
    return m.group(0) if m else None


def match_all(text: str, pattern: str) -> List[str]:
    """
    匹配所有
    
    Args:
        text: 文本
        pattern: 正则模式
        
    Returns:
        所有匹配的列表
    """
    return re.findall(pattern, text)


def match_groups(text: str, pattern: str) -> List[tuple]:
    """
    获取所有捕获组
    
    Args:
        text: 文本
        pattern: 正则模式
        
    Returns:
        捕获组列表
    """
    result = []
    for m in re.finditer(pattern, text):
        result.append(m.groups())
    return result


def replace(text: str, pattern: str, replacement: str) -> str:
    """
    替换
    
    Args:
        text: 文本
        pattern: 正则模式
        replacement: 替换内容
        
    Returns:
        替换后的文本
    """
    return re.sub(pattern, replacement, text)


def replace_all(text: str, pattern: str, replacement: str) -> str:
    """replace的别名"""
    return replace(text, pattern, replacement)


def split(text: str, pattern: str) -> List[str]:
    """
    分割
    
    Args:
        text: 文本
        pattern: 正则模式
        
    Returns:
        分割后的列表
    """
    return re.split(pattern, text)


def test(text: str, pattern: str) -> bool:
    """
    测试匹配
    
    Args:
        text: 文本
        pattern: 正则模式
        
    Returns:
        是否匹配
    """
    return bool(re.search(pattern, text))


def extract(text: str, pattern: str, group: int = 0) -> Optional[str]:
    """
    提取捕获组
    
    Args:
        text: 文本
        pattern: 正则模式
        group: 捕获组索引
        
    Returns:
        捕获的字符串或None
    """
    m = re.search(pattern, text)
    return m.group(group) if m and m.groups() else None


# 常用正则
class Patterns:
    """常用正则模式"""
    
    EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    URL = r'https?://[^\s]+'
    IP = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    DATE_ISO = r'\d{4}-\d{2}-\d{2}'
    DATE_US = r'\d{2}/\d{2}/\d{4}'
    TIME = r'\d{2}:\d{2}(:\d{2})?'
    UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    HEX_COLOR = r'#[0-9a-fA-F]{6}'
    ZIP_CODE = r'\b\d{5}(-\d{4})?\b'
    CREDIT_CARD = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    
    # 中文相关
    CHINESE = r'[\u4e00-\u9fff]+'
    CHINESE_NAME = r'[\u4e00-\u9fff]{2,4}'
    
    # 数字
    INTEGER = r'-?\d+'
    FLOAT = r'-?\d+\.\d+'
    PERCENTAGE = r'\d+(\.\d+)?%'


def is_email(text: str) -> bool:
    """是否为邮箱"""
    return test(text, Patterns.EMAIL)


def is_phone(text: str) -> bool:
    """是否为电话"""
    return test(text, Patterns.PHONE)


def is_url(text: str) -> bool:
    """是否为URL"""
    return test(text, Patterns.URL)


def is_ip(text: str) -> bool:
    """是否为IP"""
    return test(text, Patterns.IP)


def is_uuid(text: str) -> bool:
    """是否为UUID"""
    return test(text, Patterns.UUID)


# 导出
__all__ = [
    "compile",
    "match",
    "match_all",
    "match_groups",
    "replace",
    "replace_all",
    "split",
    "test",
    "extract",
    "Patterns",
    "is_email",
    "is_phone",
    "is_url",
    "is_ip",
    "is_uuid",
]
