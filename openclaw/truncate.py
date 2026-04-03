"""
OpenClaw Truncate Utilities
=========================
Inspired by Claude Code's src/utils/truncate.ts.

文本截断工具，支持：
1. 宽度感知（CJK/emoji 正确计算）
2. 路径截断（保留目录和文件名）
3. 文本截断（头部/尾部保留）
4. 自动省略号
"""

from __future__ import annotations

import re
from typing import Optional

# ============================================================================
# 宽度计算
# ============================================================================

def string_width(text: str) -> int:
    """
    计算文本显示宽度（终端列数）
    
    - ASCII: 1 列
    - CJK（中日韩字符）: 2 列
    - emoji: 2 列
    """
    width = 0
    for char in text:
        # CJK 范围
        if '\u4e00' <= char <= '\u9fff':
            width += 2
        elif '\u3000' <= char <= '\u303f':  # CJK 标点
            width += 2
        elif '\uff00' <= char <= '\uffef':  # 全角字符
            width += 2
        elif '\u0000' <= char <= '\u001f':  # 控制字符
            width += 0
        else:
            width += 1
    return width

def truncate_to_width(text: str, max_width: int) -> str:
    """
    截断文本到指定宽度，添加省略号
    
    宽度感知：CJK 字符按 2 列计算
    """
    if max_width <= 0:
        return ""
    
    if string_width(text) <= max_width:
        return text
    
    if max_width == 1:
        return "…"
    
    width = 0
    result = []
    
    for char in text:
        char_width = string_width(char)
        
        if width + char_width > max_width - 1:  # -1 for ellipsis
            break
        
        result.append(char)
        width += char_width
    
    return "".join(result) + "…"

def truncate_start_to_width(text: str, max_width: int) -> str:
    """
    从开头截断，保留尾部，添加省略号
    """
    if string_width(text) <= max_width:
        return text
    
    if max_width == 1:
        return "…"
    
    # 从后向前计算
    chars = list(text)
    width = 0
    start_idx = len(chars)
    
    for i in range(len(chars) - 1, -1, -1):
        char_width = string_width(chars[i])
        if width + char_width > max_width - 1:
            break
        width += char_width
        start_idx = i
    
    return "…" + "".join(chars[start_idx:])

def truncate_path_middle(path: str, max_width: int) -> str:
    """
    截断路径，保留目录和文件名
    
    例如：
    "src/components/deeply/nested/Foo.tsx" 
    → "src/components/…/Foo.tsx" (max_width=30)
    """
    if string_width(path) <= max_width:
        return path
    
    if max_width <= 0:
        return "…"
    
    if max_width < 5:
        return truncate_to_width(path, max_width)
    
    # 提取文件名
    last_slash = path.rfind('/')
    if last_slash >= 0:
        filename = path[last_slash:]
        directory = path[:last_slash]
    else:
        filename = path
        directory = ""
    
    filename_width = string_width(filename)
    
    # 文件名太长，从开头截断
    if filename_width >= max_width - 1:
        return truncate_start_to_width(path, max_width)
    
    # 目录可用空间
    available = max_width - 1 - filename_width  # -1 for ellipsis
    
    if available <= 0:
        return truncate_start_to_width(filename, max_width)
    
    # 截断目录并组合
    truncated_dir = truncate_to_width_no_ellipsis(directory, available)
    return truncated_dir + "…" + filename

def truncate_to_width_no_ellipsis(text: str, max_width: int) -> str:
    """
    截断文本，不添加省略号
    """
    if string_width(text) <= max_width:
        return text
    
    if max_width <= 0:
        return ""
    
    width = 0
    result = []
    
    for char in text:
        char_width = string_width(char)
        if width + char_width > max_width:
            break
        result.append(char)
        width += char_width
    
    return "".join(result)

def truncate(text: str, max_width: int, single_line: bool = False) -> str:
    """
    通用截断
    
    Args:
        text: 文本
        max_width: 最大宽度
        single_line: 是否截断到单行（处理换行符）
    """
    result = text
    
    # 单行处理
    if single_line:
        newline_idx = result.find('\n')
        if newline_idx != -1:
            result = result[:newline_idx]
            if string_width(result) + 1 > max_width:
                return truncate_to_width(result, max_width)
            return result + "…"
    
    if string_width(result) <= max_width:
        return result
    
    return truncate_to_width(result, max_width)

def wrap_text(text: str, width: int) -> list[str]:
    """
    文本换行
    
    按指定宽度分行，保留完整字符
    """
    lines = []
    current_line = ""
    current_width = 0
    
    for char in text:
        char_width = string_width(char)
        
        if current_width + char_width <= width:
            current_line += char
            current_width += char_width
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
            current_width = char_width
    
    if current_line:
        lines.append(current_line)
    
    return lines

# ============================================================================
# 交易专用截断
# ============================================================================

def truncate_stock_code(code: str, max_width: int = 8) -> str:
    """截断股票代码"""
    return truncate_to_width(code, max_width)

def truncate_reason(reason: str, max_width: int = 30) -> str:
    """截断交易理由"""
    return truncate_to_width(reason, max_width)

def truncate_message(message: str, max_width: int = 50) -> str:
    """截断消息"""
    return truncate(message, max_width, single_line=True)
