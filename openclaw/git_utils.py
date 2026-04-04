"""
Git Utilities - Git工具
基于 Claude Code git.ts 设计

Git仓库操作工具。
"""
import os
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple


GIT_ROOT_NOT_FOUND = Symbol('git-root-not-found')


def find_git_root(start_path: str) -> Optional[str]:
    """
    查找Git仓库根目录
    
    Args:
        start_path: 起始路径
        
    Returns:
        Git根目录或None
    """
    current = os.path.abspath(start_path)
    root = os.path.dirname(current)
    
    while current != root:
        git_path = os.path.join(current, '.git')
        if os.path.exists(git_path):
            return current
        
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    
    # 检查根目录
    if os.path.exists(os.path.join(root, '.git')):
        return root
    
    return None


def is_git_repository(path: str) -> bool:
    """
    检查路径是否为Git仓库
    
    Args:
        path: 路径
        
    Returns:
        是否为Git仓库
    """
    return find_git_root(path) is not None


def get_git_branch(path: str) -> Optional[str]:
    """
    获取当前分支名
    
    Args:
        path: 路径
        
    Returns:
        分支名或None
    """
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_remote_url(path: str) -> Optional[str]:
    """
    获取远程仓库URL
    
    Args:
        path: 路径
        
    Returns:
        远程URL或None
    """
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_status(path: str) -> dict:
    """
    获取Git状态
    
    Args:
        path: 路径
        
    Returns:
        状态字典
    """
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return {
                'clean': len(lines) == 0,
                'files': [line.strip() for line in lines],
            }
    except Exception:
        pass
    return {'clean': True, 'files': []}


def get_current_commit_hash(path: str) -> Optional[str]:
    """
    获取当前提交hash
    
    Args:
        path: 路径
        
    Returns:
        短hash或None
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_diff(path: str, target: str = 'HEAD') -> str:
    """
    获取Git差异
    
    Args:
        path: 路径
        target: 比较目标
        
    Returns:
        diff字符串
    """
    try:
        result = subprocess.run(
            ['git', 'diff', target],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout
    except Exception:
        return ''


def is_shallow_clone(path: str) -> bool:
    """
    检查是否为浅克隆
    
    Args:
        path: 路径
        
    Returns:
        是否为浅克隆
    """
    git_dir = os.path.join(path, '.git')
    shallow_file = os.path.join(git_dir, 'shallow')
    return os.path.exists(shallow_file)


def get_workspace_name_from_remote(remote_url: str) -> Optional[str]:
    """
    从远程URL提取工作区名称
    
    Args:
        remote_url: 远程URL
        
    Returns:
        工作区名称
    """
    if not remote_url:
        return None
    
    # 处理GitHub格式
    if 'github.com' in remote_url:
        parts = remote_url.rstrip('/').split('/')
        if len(parts) >= 2:
            return parts[-1].replace('.git', '')
    
    # 处理其他格式
    parts = remote_url.rstrip('/').split('/')
    if parts:
        return parts[-1].replace('.git', '')
    
    return None


# 导出
__all__ = [
    "GIT_ROOT_NOT_FOUND",
    "find_git_root",
    "is_git_repository",
    "get_git_branch",
    "get_git_remote_url",
    "get_git_status",
    "get_current_commit_hash",
    "get_git_diff",
    "is_shallow_clone",
    "get_workspace_name_from_remote",
]
