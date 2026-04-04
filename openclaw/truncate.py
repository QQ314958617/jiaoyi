"""
Truncate - 字符串截断工具
基于 Claude Code truncate.ts 设计

提供宽度感知的字符串截断功能。
"""
import re
from typing import Optional


def string_width(s: str) -> int:
    """
    计算字符串的显示宽度（终端列数）
    
    Args:
        s: 字符串
        
    Returns:
        显示宽度
    """
    width = 0
    for c in s:
        # CJK字符宽度为2
        if '\u4e00' <= c <= '\u9fff':
            width += 2
        # 全角字符宽度为2
        elif '\uff00' <= c <= '\uffef':
            width += 2
        # 其他ASCII字符宽度为1
        else:
            width += 1
    return width


def truncate_path_middle(path: str, max_length: int) -> str:
    """
    在路径中间截断，保留目录上下文和文件名
    
    例如: "src/components/deeply/nested/folder/MyComponent.tsx"
    变成 (max_length=30): "src/components/…/MyComponent.tsx"
    
    Args:
        path: 文件路径
        max_length: 最大显示宽度
        
    Returns:
        截断后的路径
    """
    if string_width(path) <= max_length:
        return path
    
    if max_length <= 0:
        return '…'
    
    if max_length < 5:
        return truncate_to_width(path, max_length)
    
    # 找到文件名
    last_slash = path.rfind('/')
    if last_slash >= 0:
        filename = path[last_slash:]
        directory = path[:last_slash]
    else:
        filename = path
        directory = ''
    
    filename_width = string_width(filename)
    
    # 文件名太长
    if filename_width >= max_length - 1:
        return truncate_start_to_width(path, max_length)
    
    # 计算可用宽度
    available = max_length - 1 - filename_width  # -1 for ellipsis
    
    if available <= 0:
        return truncate_start_to_width(filename, max_length)
    
    # 截断目录
    truncated_dir = truncate_to_width_no_ellipsis(directory, available)
    return truncated_dir + '…' + filename


def truncate_to_width(s: str, max_width: int) -> str:
    """
    截断字符串到最大显示宽度
    
    Args:
        s: 字符串
        max_width: 最大宽度
        
    Returns:
        截断后的字符串
    """
    if string_width(s) <= max_width:
        return s
    
    result = []
    current_width = 0
    
    for c in s:
        char_width = char_display_width(c)
        if current_width + char_width > max_width:
            break
        result.append(c)
        current_width += char_width
    
    return ''.join(result) + '…'


def truncate_to_width_no_ellipsis(s: str, max_width: int) -> str:
    """
    截断字符串到最大宽度（不加省略号）
    
    Args:
        s: 字符串
        max_width: 最大宽度
        
    Returns:
        截断后的字符串
    """
    if string_width(s) <= max_width:
        return s
    
    result = []
    current_width = 0
    
    for c in s:
        char_width = char_display_width(c)
        if current_width + char_width > max_width:
            break
        result.append(c)
        current_width += char_width
    
    return ''.join(result)


def truncate_start_to_width(s: str, max_width: int) -> str:
    """
    从开头截断字符串
    
    Args:
        s: 字符串
        max_width: 最大宽度
        
    Returns:
        截断后的字符串
    """
    if string_width(s) <= max_width:
        return s
    
    # 反转字符串，找到尾部
    reversed_s = s[::-1]
    truncated = truncate_to_width_no_ellipsis(reversed_s, max_width)
    return '…' + truncated[::-1]


def char_display_width(c: str) -> int:
    """
    获取字符的显示宽度
    
    Args:
        c: 字符
        
    Returns:
        宽度（1或2）
    """
    # CJK
    if '\u4e00' <= c <= '\u9fff':
        return 2
    # 全角
    if '\uff00' <= c <= '\uffef':
        return 2
    # Emoji等宽字符（简化处理）
    if ord(c) > 0xFFFF:
        return 2
    return 1


# 导出
__all__ = [
    "string_width",
    "truncate_path_middle",
    "truncate_to_width",
    "truncate_to_width_no_ellipsis",
    "truncate_start_to_width",
    "char_display_width",
]
