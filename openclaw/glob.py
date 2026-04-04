"""
Glob - 文件模式匹配
基于 Claude Code glob.ts 设计

Glob模式匹配工具。
"""
import os
import fnmatch
from typing import List


def match(filename: str, pattern: str) -> bool:
    """
    匹配文件名
    
    Args:
        filename: 文件名
        pattern: glob模式 (*.txt, *.py)
    """
    return fnmatch.fnmatch(filename, pattern)


def filter_(items: List[str], pattern: str) -> List[str]:
    """
    过滤列表
    
    Args:
        items: 文件名列表
        pattern: glob模式
        
    Returns:
        匹配的文件
    """
    return [item for item in items if match(item, pattern)]


def glob(pattern: str, cwd: str = None) -> List[str]:
    """
    获取匹配的文件
    
    Args:
        pattern: glob模式 (如 **/*.py, *.txt)
        cwd: 工作目录
    """
    import pathlib
    
    # 解析pattern
    if cwd:
        base = pathlib.Path(cwd)
    else:
        base = pathlib.Path.cwd()
    
    # 处理**模式
    if '**' in pattern:
        parts = pattern.split('**')
        base_path = base / parts[0].strip('/\\')
        rest_pattern = parts[1].strip('/\\')
        
        results = []
        if base_path.exists():
            for path in base_path.rglob('*'):
                if rest_pattern:
                    if fnmatch.fnmatch(path.name, rest_pattern):
                        results.append(str(path))
                else:
                    results.append(str(path))
        return results
    else:
        # 简单glob
        parent = base
        filename_pattern = os.path.basename(pattern)
        
        if '/' in pattern or '\\' in pattern:
            parent = base / os.path.dirname(pattern)
            if not parent.exists():
                return []
        
        results = []
        if parent.exists():
            for item in parent.iterdir():
                if fnmatch.fnmatch(item.name, filename_pattern):
                    results.append(str(item))
        
        return results


def glob_recursive(pattern: str, cwd: str = None) -> List[str]:
    """
    递归glob
    """
    import pathlib
    
    if cwd:
        base = pathlib.Path(cwd)
    else:
        base = pathlib.Path.cwd()
    
    # 解析模式
    if '/' in pattern:
        parts = pattern.rsplit('/', 1)
        dir_pattern = parts[0]
        file_pattern = parts[1]
    else:
        dir_pattern = '**'
        file_pattern = pattern
    
    results = []
    
    if dir_pattern == '**':
        for path in base.rglob(file_pattern):
            if path.is_file():
                results.append(str(path))
    else:
        dir_path = base / dir_pattern
        if dir_path.exists():
            for path in dir_path.rglob(file_pattern):
                if path.is_file():
                    results.append(str(path))
    
    return results


def expand(pattern: str, cwd: str = None) -> List[str]:
    """展开模式"""
    return glob_recursive(pattern, cwd)


# 导出
__all__ = [
    "match",
    "filter_",
    "glob",
    "glob_recursive",
    "expand",
]
