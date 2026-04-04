"""
Diff - 差异
基于 Claude Code diff.ts 设计

文本差异工具。
"""
from typing import List, Tuple


def diff_lines(old: str, new: str) -> List[Tuple[int, str]]:
    """
    计算行差异
    
    Args:
        old: 旧文本
        new: 新文本
        
    Returns:
        [(类型, 行)] 列表
        类型: 0=相同, 1=新增, -1=删除
    """
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    
    result = []
    
    # 简单的行对齐算法
    lcs = _lcs(old_lines, new_lines)
    
    old_idx = 0
    new_idx = 0
    lcs_idx = 0
    
    while old_idx < len(old_lines) or new_idx < len(new_lines):
        if (lcs_idx < len(lcs) and 
            old_idx < len(old_lines) and 
            new_idx < len(new_lines) and
            old_lines[old_idx] == lcs[lcs_idx] and
            new_lines[new_idx] == lcs[lcs_idx]):
            result.append((0, old_lines[old_idx]))
            old_idx += 1
            new_idx += 1
            lcs_idx += 1
        elif (new_idx < len(new_lines) and 
              (lcs_idx >= len(lcs) or new_lines[new_idx] != lcs[lcs_idx])):
            result.append((1, new_lines[new_idx]))
            new_idx += 1
        elif old_idx < len(old_lines):
            result.append((-1, old_lines[old_idx]))
            old_idx += 1
    
    return result


def _lcs(a: List, b: List) -> List:
    """最长公共子序列"""
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # 回溯
    result = []
    i, j = m, n
    while i > 0 and j > 0:
        if a[i-1] == b[j-1]:
            result.append(a[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    return list(reversed(result))


def diff_words(old: str, new: str) -> List[Tuple[int, str]]:
    """
    计算单词差异
    
    Returns:
        [(类型, 词)]
    """
    old_words = old.split()
    new_words = new.split()
    
    result = []
    lcs = _lcs(old_words, new_words)
    
    old_idx = 0
    new_idx = 0
    lcs_idx = 0
    
    while old_idx < len(old_words) or new_idx < len(new_words):
        if (lcs_idx < len(lcs) and 
            old_idx < len(old_words) and 
            new_idx < len(new_words) and
            old_words[old_idx] == lcs[lcs_idx] and
            new_words[new_idx] == lcs[lcs_idx]):
            result.append((0, old_words[old_idx]))
            old_idx += 1
            new_idx += 1
            lcs_idx += 1
        elif new_idx < len(new_words):
            result.append((1, new_words[new_idx]))
            new_idx += 1
        elif old_idx < len(old_words):
            result.append((-1, old_words[old_idx]))
            old_idx += 1
    
    return result


def format_diff(lines: List[Tuple[int, str]], 
                add_prefix: str = "+ ",
                del_prefix: str = "- ") -> str:
    """
    格式化差异输出
    
    Args:
        lines: 差异列表
        add_prefix: 新增行前缀
        del_prefix: 删除行前缀
        
    Returns:
        格式化字符串
    """
    result = []
    for type_, line in lines:
        if type_ == 0:
            result.append(f"  {line}")
        elif type_ == 1:
            result.append(f"{add_prefix}{line}")
        else:
            result.append(f"{del_prefix}{line}")
    return '\n'.join(result)


# 导出
__all__ = [
    "diff_lines",
    "diff_words",
    "format_diff",
]
