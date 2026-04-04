"""
Which - 命令查找工具
基于 Claude Code which.ts 设计

查找命令的完整路径。
"""
import os
import shutil
import stat
from typing import Optional


def which(command: str) -> Optional[str]:
    """
    异步查找命令路径（实际是同步）
    
    Args:
        command: 命令名
        
    Returns:
        命令的完整路径，未找到返回None
    """
    # 优先使用shutil.which（Python 3.3+）
    result = shutil.which(command)
    if result:
        return result
    
    # Windows回退
    if os.name == 'nt':
        return _which_windows(command)
    
    return None


def which_sync(command: str) -> Optional[str]:
    """
    同步查找命令路径
    
    Args:
        command: 命令名
        
    Returns:
        命令的完整路径，未找到返回None
    """
    return which(command)


def _which_windows(command: str) -> Optional[str]:
    """
    Windows命令查找
    
    Args:
        command: 命令名
        
    Returns:
        命令路径
    """
    import subprocess
    
    try:
        result = subprocess.run(
            f'where.exe {command}',
            shell=True,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout:
            # 返回第一个结果
            return result.stdout.strip().split('\n')[0]
    except Exception:
        pass
    
    return None


def is_executable(path: str) -> bool:
    """
    检查路径是否为可执行文件
    
    Args:
        path: 文件路径
        
    Returns:
        是否可执行
    """
    try:
        return os.path.isfile(path) and os.access(path, os.X_OK)
    except Exception:
        return False


def find_in_path(command: str) -> Optional[str]:
    """
    在PATH中查找命令
    
    Args:
        command: 命令名
        
    Returns:
        找到的路径或None
    """
    path_env = os.environ.get('PATH', os.defpath)
    path_dirs = path_env.split(os.pathsep)
    
    for directory in path_dirs:
        candidate = os.path.join(directory, command)
        # Windows下也检查.exe
        if not os.name == 'nt':
            if is_executable(candidate):
                return candidate
        else:
            # Windows下尝试添加各种扩展名
            for ext in ['', '.exe', '.bat', '.cmd', '.com']:
                candidate_ext = candidate + ext
                if os.path.isfile(candidate_ext):
                    return candidate_ext
    
    return None


# 导出
__all__ = [
    "which",
    "which_sync",
    "is_executable",
    "find_in_path",
]
