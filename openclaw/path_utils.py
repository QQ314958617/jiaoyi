"""
Path Utilities - 路径工具
基于 Claude Code path.ts 设计

提供路径处理、扩展、规范化等功能。
"""
import os
import re
from pathlib import Path
from typing import Optional


def expand_path(path: str, base_dir: Optional[str] = None) -> str:
    """
    扩展路径，支持~和相对路径
    
    Args:
        path: 要扩展的路径
        base_dir: 基础目录，默认为当前工作目录
        
    Returns:
        扩展后的绝对路径
    """
    # 默认使用当前工作目录
    if not base_dir:
        base_dir = os.getcwd()
    
    if not path or not isinstance(path, str):
        raise TypeError(f"Path must be a string, received {type(path)}")
    
    # 检查空字节
    if '\0' in path or '\0' in base_dir:
        raise ValueError("Path contains null bytes")
    
    path = path.strip()
    if not path:
        return os.path.normpath(base_dir)
    
    # 处理home目录
    if path == '~':
        return os.path.normpath(os.path.expanduser('~'))
    
    if path.startswith('~/'):
        return os.path.normpath(os.path.join(os.path.expanduser('~'), path[2:]))
    
    # 处理绝对路径
    if os.path.isabs(path):
        return os.path.normpath(path)
    
    # 处理相对路径
    return os.path.normpath(os.path.join(base_dir, path))


def to_relative_path(absolute_path: str, base_dir: Optional[str] = None) -> str:
    """
    将绝对路径转换为相对路径
    
    Args:
        absolute_path: 绝对路径
        base_dir: 基准目录，默认为当前工作目录
        
    Returns:
        相对路径（如果在基准目录下）或原绝对路径
    """
    if not base_dir:
        base_dir = os.getcwd()
    
    try:
        rel = os.path.relpath(absolute_path, base_dir)
        # 如果相对路径以..开头，说明在基准目录外，保持绝对路径
        if rel.startswith('..'):
            return absolute_path
        return rel
    except ValueError:
        # 不同驱动器等情况下返回原路径
        return absolute_path


def sanitize_path(path: str) -> str:
    """
    清理路径，移除不安全的字符和序列
    
    Args:
        path: 要清理的路径
        
    Returns:
        清理后的路径
    """
    # 移除null字节
    path = path.replace('\0', '')
    
    # 标准化路径分隔符
    path = path.replace('\\', '/')
    
    # 移除多余的斜杠
    while '//' in path:
        path = path.replace('//', '/')
    
    # 移除 . 目录引用（保持 .. 以防超出范围）
    parts = []
    for part in path.split('/'):
        if part == '.':
            continue
        elif part == '..':
            # 不在这里处理，留给os.path处理
            if parts:
                parts.pop()
        else:
            parts.append(part)
    
    result = '/'.join(parts)
    
    # 保持原始的根路径
    if path.startswith('/'):
        result = '/' + result
    
    return result


def contains_path_traversal(path: str) -> bool:
    """
    检查路径是否包含路径遍历攻击序列
    
    Args:
        path: 要检查的路径
        
    Returns:
        是否包含..序列
    """
    # 规范化后检查
    normalized = os.path.normpath(path)
    return normalized.startswith('..')


def get_directory_for_path(path: str) -> str:
    """
    获取路径的目录部分
    
    Args:
        path: 文件路径
        
    Returns:
        目录路径
    """
    return os.path.dirname(os.path.abspath(expand_path(path)))


def is_subpath(path: str, parent: str) -> bool:
    """
    检查path是否为parent的子路径
    
    Args:
        path: 要检查的路径
        parent: 父路径
        
    Returns:
        是否为子路径
    """
    path_abs = os.path.abspath(expand_path(path))
    parent_abs = os.path.abspath(expand_path(parent))
    
    return path_abs.startswith(parent_abs + os.sep) or path_abs == parent_abs


def normalize_case_for_comparison(path: str) -> str:
    """
    规范化路径大小写用于比较
    
    Args:
        path: 路径
        
    Returns:
        小写路径
    """
    return path.lower()


# 导出
__all__ = [
    "expand_path",
    "to_relative_path",
    "sanitize_path",
    "contains_path_traversal",
    "get_directory_for_path",
    "is_subpath",
    "normalize_case_for_comparison",
]
