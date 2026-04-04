"""
Diff - 差异比较
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
        [(类型, 行)]
        类型: 0=相同, 1=新增, -1=删除
    """
    old_lines = old.splitlines()
    new_lines = new.splitlines()
    
    # LCS算法
    dp = [[0] * (len(new_lines) + 1) for _ in range(len(old_lines) + 1)]
    
    for i in range(1, len(old_lines) + 1):
        for j in range(1, len(new_lines) + 1):
            if old_lines[i-1] == new_lines[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    # 回溯找LCS
    result = []
    i, j = len(old_lines), len(new_lines)
    lcs = []
    
    while i > 0 and j > 0:
        if old_lines[i-1] == new_lines[j-1]:
            lcs.append(old_lines[i-1])
            i -= 1
            j -= 1
        elif dp[i-1][j] > dp[i][j-1]:
            i -= 1
        else:
            j -= 1
    
    lcs.reverse()
    
    # 遍历生成差异
    result = []
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
        elif new_idx < len(new_lines):
            result.append((1, new_lines[new_idx]))
            new_idx += 1
        elif old_idx < len(old_lines):
            result.append((-1, old_lines[old_idx]))
            old_idx += 1
    
    return result


def diff_words(old: str, new: str) -> List[Tuple[int, str]]:
    """计算单词差异"""
    return diff_lines(old, new)


def format_diff(lines: List[Tuple[int, str]]) -> str:
    """格式化差异"""
    result = []
    for type_, line in lines:
        if type_ == 0:
            result.append(f"  {line}")
        elif type_ == 1:
            result.append(f"+ {line}")
        else:
            result.append(f"- {line}")
    return '\n'.join(result)


# 导出
__all__ = [
    "diff_lines",
    "diff_words",
    "format_diff",
]
