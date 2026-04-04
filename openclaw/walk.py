"""
Walk - 遍历
基于 Claude Code walk.ts 设计

目录遍历工具。
"""
import os
from typing import List, Callable


def walk_dir(path: str, pattern: str = None) -> List[str]:
    """
    遍历目录
    
    Args:
        path: 目录路径
        pattern: 可选的文件过滤模式
        
    Returns:
        文件路径列表
    """
    results = []
    
    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = os.path.join(root, name)
            if pattern is None or _matches(file_path, pattern):
                results.append(file_path)
    
    return results


def _matches(path: str, pattern: str) -> bool:
    """简单模式匹配"""
    import fnmatch
    return fnmatch.fnmatch(os.path.basename(path), pattern)


def walk_dir_recursive(path: str, max_depth: int = None) -> List[str]:
    """
    递归遍历目录
    
    Args:
        path: 目录路径
        max_depth: 最大深度
        
    Returns:
        所有文件路径
    """
    results = []
    _walk_recursive(path, results, 0, max_depth)
    return results


def _walk_recursive(path: str, results: List, depth: int, max_depth: int) -> None:
    """递归遍历"""
    if max_depth is not None and depth >= max_depth:
        return
    
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                results.append(entry.path)
            elif entry.is_dir():
                _walk_recursive(entry.path, results, depth + 1, max_depth)
    except PermissionError:
        pass


def find_files(path: str, name: str) -> List[str]:
    """
    查找文件
    
    Args:
        path: 目录路径
        name: 文件名
        
    Returns:
        匹配的文件路径
    """
    results = []
    for root, dirs, files in os.walk(path):
        if name in files:
            results.append(os.path.join(root, name))
    return results


def find_dirs(path: str, name: str) -> List[str]:
    """
    查找目录
    
    Args:
        path: 目录路径
        name: 目录名
        
    Returns:
        匹配的目录路径
    """
    results = []
    for root, dirs, files in os.walk(path):
        if name in dirs:
            results.append(os.path.join(root, name))
    return results


def tree(path: str, max_depth: int = None, prefix: str = "") -> str:
    """
    目录树
    
    Returns:
        树形字符串
    """
    lines = []
    
    try:
        entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name))
    except PermissionError:
        return prefix + "[Permission Denied]\n"
    
    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        current_prefix = "└── " if is_last else "├── "
        lines.append(prefix + current_prefix + entry.name)
        
        if entry.is_dir():
            extension = "    " if is_last else "│   "
            lines.append(tree(entry.path, max_depth, prefix + extension))
    
    return '\n'.join(lines)


# 导出
__all__ = [
    "walk_dir",
    "walk_dir_recursive",
    "find_files",
    "find_dirs",
    "tree",
]
