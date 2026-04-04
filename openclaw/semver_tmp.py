"""
Diff - 差异计算
基于 Claude Code diff.ts 设计

文本差异工具。
"""
from typing import List, Tuple


def diff_strings(old: str, new: str) -> List[Tuple[str, str]]:
    """
    计算字符串差异
    
    Args:
        old: 旧字符串
        new: 新字符串
        
    Returns:
        [(类型, 值), ...] 类型: 'same', 'add', 'remove'
    """
    result = []
    
    old_lines = old.split('\n')
    new_lines = new.split('\n')
    
    # 简单的行级diff
    lcs = _longest_common_subsequence(old_lines, new_lines)
    
    old_idx = 0
    new_idx = 0
    lcs_idx = 0
    
    while old_idx < len(old_lines) or new_idx < len(new_lines):
        if (lcs_idx < len(lcs) and 
            old_idx < len(old_lines) and 
            new_idx < len(new_lines) and
            old_lines[old_idx] == lcs[lcs_idx] and
            new_lines[new_idx] == lcs[lcs_idx]):
            
            result.append(('same', old_lines[old_idx]))
            old_idx += 1
            new_idx += 1
            lcs_idx += 1
        
        elif (new_idx < len(new_lines) and 
              (lcs_idx >= len(lcs) or new_lines[new_idx] != lcs[lcs_idx])):
            result.append(('add', new_lines[new_idx]))
            new_idx += 1
        
        elif (old_idx < len(old_lines) and 
              (lcs_idx >= len(lcs) or old_lines[old_idx] != lcs[lcs_idx])):
            result.append(('remove', old_lines[old_idx]))
            old_idx += 1
    
    return result


def _longest_common_subsequence(a: List[str], b: List[str]) -> List[str]:
    """计算最长公共子序列"""
    m, n = len(a), len(b)
    
    # 动态规划表
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # 回溯找LCS
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


def diff_lines(old_lines: List[str], new_lines: List[str]) -> List[Tuple[str, str]]:
    """
    计算行差异
    
    Returns:
        [(类型, 行), ...]
    """
    return diff_strings('\n'.join(old_lines), '\n'.join(new_lines))


def format_diff(diff_result: List[Tuple[str, str]]) -> str:
    """
    格式化差异输出
    
    Args:
        diff_result: diff_strings的返回值
        
    Returns:
        格式化后的字符串
    """
    lines = []
    
    for change_type, value in diff_result:
        if change_type == 'same':
            lines.append(f"  {value}")
        elif change_type == 'add':
            lines.append(f"+ {value}")
        elif change_type == 'remove':
            lines.append(f"- {value}")
    
    return '\n'.join(lines)


class DiffResult:
    """差异结果"""
    
    def __init__(self, old: str, new: str):
        self.old = old
        self.new = new
        self._changes = diff_strings(old, new)
    
    @property
    def changes(self) -> List[Tuple[str, str]]:
        return self._changes
    
    @property
    def added_lines(self) -> List[str]:
        return [v for t, v in self._changes if t == 'add']
    
    @property
    def removed_lines(self) -> List[str]:
        return [v for t, v in self._changes if t == 'remove']
    
    @property
    def unchanged_lines(self) -> List[str]:
        return [v for t, v in self._changes if t == 'same']
    
    def __str__(self) -> str:
        return format_diff(self._changes)


# 导出
__all__ = [
    "diff_strings",
    "diff_lines",
    "format_diff",
    "DiffResult",
]
