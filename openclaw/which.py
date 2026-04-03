"""
OpenClaw Which Utility
==================
Inspired by Claude Code's src/utils/which.ts.

which 命令实现，支持：
1. 查找命令路径
2. 检查命令是否存在
3. 跨平台支持
"""

from __future__ import annotations

import os, shutil
from typing import Optional

# ============================================================================
# which
# ============================================================================

def which(command: str) -> Optional[str]:
    """
    查找命令的完整路径
    
    Args:
        command: 命令名
    
    Returns:
        命令路径，如果不存在返回 None
    
    Example:
        >>> which("python3")
        '/usr/bin/python3'
        >>> which("nonexistent")
        None
    """
    # shutil.which 已经实现了跨平台的命令查找
    path = shutil.which(command)
    return path

def which_sync(command: str) -> Optional[str]:
    """which 的同步版本（与 which 相同）"""
    return which(command)

def which_all(command: str) -> list[str]:
    """
    查找命令的所有路径
    
    Returns:
        所有匹配的路径列表
    """
    # 获取 PATH 环境变量
    path_env = os.environ.get("PATH", os.defpath)
    if not path_env:
        return []
    
    results = []
    path_dirs = path_env.split(os.pathsep)
    
    # Windows 上也检查 .exe 后缀
    suffixes = ("",)  # 默认无后缀
    
    if os.name == "nt" or os.name == "ce":
        # Windows: 检查常见可执行后缀
        suffixes = ("", ".exe", ".bat", ".cmd", ".com")
        
        # 也检查 PATHEXT 环境变量
        pathext = os.environ.get("PATHEXT", "")
        if pathext:
            suffixes = tuple([""] + pathext.split(os.pathsep))
    
    for directory in path_dirs:
        if not directory:
            continue
        
        for suffix in suffixes:
            full_path = os.path.join(directory, command + suffix)
            
            # 检查文件是否存在且可执行
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                if full_path not in results:
                    results.append(full_path)
    
    return results

def exists(command: str) -> bool:
    """
    检查命令是否存在
    
    Example:
        >>> exists("python3")
        True
        >>> exists("nonexistent")
        False
    """
    return which(command) is not None

def require(command: str) -> str:
    """
    获取命令路径，不存在则抛出异常
    
    Raises:
        FileNotFoundError: 命令不存在
    """
    path = which(command)
    if path is None:
        raise FileNotFoundError(f"Command not found: {command}")
    return path

# ============================================================================
# where (Windows 特有)
# ============================================================================

def where(command: str) -> list[str]:
    """
    Windows 风格的 where 命令
    
    返回所有匹配的命令路径
    
    Example:
        >>> where("python")
        ['C:\\Python39\\python.exe', 'C:\\Python39\\python3.exe']
    """
    return which_all(command)

# ============================================================================
# which with custom PATH
# ============================================================================

def which_with_path(command: str, path: str) -> Optional[str]:
    """
    使用指定的 PATH 查找命令
    
    Args:
        command: 命令名
        path: 自定义的 PATH 字符串
    """
    # 保存原始 PATH
    original_path = os.environ.get("PATH")
    
    try:
        os.environ["PATH"] = path
        return which(command)
    finally:
        # 恢复原始 PATH
        if original_path is not None:
            os.environ["PATH"] = original_path
        else:
            os.environ.pop("PATH", None)

def which_in_dir(command: str, directory: str) -> Optional[str]:
    """
    在指定目录中查找命令
    
    只检查该目录，不检查 PATH
    """
    if os.path.isfile(command):
        if os.access(command, os.X_OK):
            return command
        return None
    
    full_path = os.path.join(directory, command)
    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
        return full_path
    
    return None
