"""
DetectRepository - 仓库检测
基于 Claude Code detect_repository.ts 设计

Git仓库检测工具。
"""
import os
import subprocess
from typing import Optional, Tuple


def is_git_repo(path: str = None) -> bool:
    """
    是否为Git仓库
    
    Args:
        path: 路径（默认当前目录）
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == "true"
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def find_repo_root(path: str = None) -> Optional[str]:
    """
    查找仓库根目录
    
    Args:
        path: 起始路径
        
    Returns:
        仓库根目录或None
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def get_remote_url(path: str = None) -> Optional[str]:
    """
    获取远程仓库URL
    
    Returns:
        origin的URL或None
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def get_branch(path: str = None) -> Optional[str]:
    """
    获取当前分支
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=path,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def detect_github_repo(path: str = None) -> Optional[Tuple[str, str]]:
    """
    检测GitHub仓库
    
    Returns:
        (owner, repo) 或 None
    """
    remote = get_remote_url(path)
    if not remote:
        return None
    
    # 解析 git@github.com:owner/repo.git 或 https://github.com/owner/repo.git
    import re
    
    ssh_pattern = r'git@github\.com:([^/]+)/(.+?)(?:\.git)?$'
    https_pattern = r'https?://github\.com/([^/]+)/(.+?)(?:\.git)?$'
    
    match = re.match(ssh_pattern, remote)
    if match:
        return match.group(1), match.group(2).replace('.git', '')
    
    match = re.match(https_pattern, remote)
    if match:
        return match.group(1), match.group(2).replace('.git', '')
    
    return None


def get_repo_info(path: str = None) -> dict:
    """
    获取仓库信息
    """
    info = {
        "is_repo": is_git_repo(path),
        "root": None,
        "remote": None,
        "branch": None,
        "github": None,
    }
    
    if info["is_repo"]:
        info["root"] = find_repo_root(path)
        info["remote"] = get_remote_url(path)
        info["branch"] = get_branch(path)
        info["github"] = detect_github_repo(path)
    
    return info


# 导出
__all__ = [
    "is_git_repo",
    "find_repo_root",
    "get_remote_url",
    "get_branch",
    "detect_github_repo",
    "get_repo_info",
]
