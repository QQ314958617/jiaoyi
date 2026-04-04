"""
Patch - 补丁
基于 Claude Code patch.ts 设计

补丁工具。
"""
from typing import List, Tuple


def create_patch(old_lines: List[str], new_lines: List[str]) -> List[Tuple[int, str]]:
    """
    创建补丁
    
    Args:
        old_lines: 旧行列表
        new_lines: 新行列表
        
    Returns:
        补丁列表 [(类型, 行)]
    """
    from .diff import diff_lines
    return diff_lines('\n'.join(old_lines), '\n'.join(new_lines))


def apply_patch(lines: List[str], patch: List[Tuple[int, str]]) -> List[str]:
    """
    应用补丁
    
    Args:
        lines: 原始行列表
        patch: 补丁列表
        
    Returns:
        打完补丁的行列表
    """
    result = []
    old_idx = 0
    
    for type_, content in patch:
        if type_ == 0:
            # 保持原行
            result.append(content)
            old_idx += 1
        elif type_ == -1:
            # 删除行（跳过原始行）
            old_idx += 1
        elif type_ == 1:
            # 新增行
            result.append(content)
    
    return result


def reverse_patch(patch: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
    """
    反转补丁
    
    Args:
        patch: 原始补丁
        
    Returns:
        反转后的补丁
    """
    result = []
    for type_, content in patch:
        if type_ == 0:
            result.append((0, content))
        elif type_ == 1:
            result.append((-1, content))
        else:
            result.append((1, content))
    return result


def merge_patches(*patches: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
    """
    合并多个补丁
    
    Args:
        *patches: 补丁列表
        
    Returns:
        合并后的补丁
    """
    result = []
    for patch in patches:
        result.extend(patch)
    return result


# 导出
__all__ = [
    "create_patch",
    "apply_patch",
    "reverse_patch",
    "merge_patches",
]
