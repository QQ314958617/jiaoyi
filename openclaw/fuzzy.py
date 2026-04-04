"""
Fuzzy - 模糊搜索
基于 Claude Code fuzzy.ts 设计

模糊搜索工具。
"""
from typing import List, Tuple


def fuzzy_match(text: str, pattern: str) -> bool:
    """
    模糊匹配
    
    Args:
        text: 文本
        pattern: 模式（可包含*和?）
    """
    import fnmatch
    return fnmatch.fnmatch(text.lower(), pattern.lower())


def fuzzy_score(text: str, pattern: str) -> int:
    """
    模糊匹配得分
    
    返回匹配字符数
    """
    text = text.lower()
    pattern = pattern.lower()
    
    score = 0
    pattern_idx = 0
    
    for char in text:
        if pattern_idx < len(pattern) and char == pattern[pattern_idx]:
            score += 1
            pattern_idx += 1
    
    return score


def fuzzy_filter(items: List[str], pattern: str) -> List[Tuple[str, int]]:
    """
    模糊过滤
    
    Returns:
        [(匹配项, 得分)] 按得分降序
    """
    results = []
    for item in items:
        if fuzzy_match(item, pattern):
            score = fuzzy_score(item, pattern)
            results.append((item, score))
    
    return sorted(results, key=lambda x: -x[1])


def fuzzy_search(text: str, pattern: str) -> List[int]:
    """
    模糊搜索返回匹配位置
    
    Returns:
        [匹配字符位置]
    """
    text = text.lower()
    pattern = pattern.lower()
    
    matches = []
    pattern_idx = 0
    
    for i, char in enumerate(text):
        if pattern_idx < len(pattern) and char == pattern[pattern_idx]:
            matches.append(i)
            pattern_idx += 1
    
    return matches if pattern_idx == len(pattern) else []


# 导出
__all__ = [
    "fuzzy_match",
    "fuzzy_score",
    "fuzzy_filter",
    "fuzzy_search",
]
