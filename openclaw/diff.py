"""
Diff - 差异计算
基于 Claude Code diff.ts 设计

计算和应用文件差异。
"""
import difflib
from dataclasses import dataclass
from typing import List, Optional, Tuple


CONTEXT_LINES = 3
DIFF_TIMEOUT_MS = 5000


@dataclass
class Hunk:
    """差异块"""
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[str]


def escape_for_diff(s: str) -> str:
    """
    转义diff专用字符
    
    Args:
        s: 字符串
        
    Returns:
        转义后的字符串
    """
    AMPERSAND_TOKEN = '<<:AMPERSAND_TOKEN:>>'
    DOLLAR_TOKEN = '<<:DOLLAR_TOKEN:>>'
    
    result = s.replace('&', AMPERSAND_TOKEN)
    result = result.replace('$', DOLLAR_TOKEN)
    return result


def unescape_from_diff(s: str) -> str:
    """
    从diff结果反转义
    
    Args:
        s: 字符串
        
    Returns:
        恢复后的字符串
    """
    AMPERSAND_TOKEN = '<<:AMPERSAND_TOKEN:>>'
    DOLLAR_TOKEN = '<<:DOLLAR_TOKEN:>>'
    
    result = s.replace(AMPERSAND_TOKEN, '&')
    result = result.replace(DOLLAR_TOKEN, '$')
    return result


def compute_unified_diff(
    old_content: str,
    new_content: str,
    old_path: str = 'original',
    new_path: str = 'modified',
    context_lines: int = CONTEXT_LINES,
) -> str:
    """
    计算统一格式差异
    
    Args:
        old_content: 原始内容
        new_content: 新内容
        old_path: 原始文件路径
        new_path: 新文件路径
        context_lines: 上下文行数
        
    Returns:
        统一格式的diff字符串
    """
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    # 确保最后一行有换行符
    if old_lines and not old_lines[-1].endswith('\n'):
        old_lines[-1] += '\n'
    if new_lines and not new_lines[-1].endswith('\n'):
        new_lines[-1] += '\n'
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=old_path,
        tofile=new_path,
        n=context_lines,
    )
    
    return ''.join(diff)


def apply_diff(content: str, diff: str) -> str:
    """
    应用差异到内容
    
    Args:
        content: 原始内容
        diff: 差异字符串
        
    Returns:
        应用差异后的内容
    """
    # 解析diff并应用（简化实现）
    lines = content.splitlines(keepends=True)
    result_lines = []
    
    diff_lines = diff.splitlines(keepends=True)
    
    i = 0
    line_num = 1
    
    for diff_line in diff_lines:
        if diff_line.startswith('@@'):
            # 解析行号
            import re
            match = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', diff_line)
            if match:
                old_start = int(match.group(1))
                new_start = int(match.group(3))
                line_num = old_start
        elif diff_line.startswith('-'):
            # 删除的行
            if i < len(lines) and lines[i].rstrip() == diff_line[1:].rstrip():
                i += 1
            line_num += 1
        elif diff_line.startswith('+'):
            # 添加的行
            result_lines.append(diff_line[1:])
        elif diff_line.startswith(' '):
            # 上下文行
            if i < len(lines):
                result_lines.append(lines[i])
                i += 1
            line_num += 1
    
    # 添加剩余行
    while i < len(lines):
        result_lines.append(lines[i])
        i += 1
    
    return ''.join(result_lines)


def count_diff_stats(diff: str) -> Tuple[int, int]:
    """
    统计差异的添加和删除行数
    
    Args:
        diff: diff字符串
        
    Returns:
        (添加行数, 删除行数)
    """
    additions = 0
    deletions = 0
    
    for line in diff.splitlines():
        if line.startswith('+') and not line.startswith('+++'):
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1
    
    return additions, deletions


# 导出
__all__ = [
    "CONTEXT_LINES",
    "DIFF_TIMEOUT_MS",
    "Hunk",
    "escape_for_diff",
    "unescape_from_diff",
    "compute_unified_diff",
    "apply_diff",
    "count_diff_stats",
]
