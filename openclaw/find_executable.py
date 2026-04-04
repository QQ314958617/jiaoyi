"""
Find Executable - 查找可执行文件
基于 Claude Code findExecutable.ts 设计

查找PATH中的可执行文件。
"""
import shutil
from typing import Tuple


def find_executable(exe: str, args: list = None) -> Tuple[str, list]:
    """
    查找可执行文件
    
    在PATH中搜索可执行文件，类似于`which`命令。
    
    Args:
        exe: 可执行文件名
        args: 参数列表
        
    Returns:
        (命令路径, 参数列表)
    """
    args = args or []
    
    resolved = shutil.which(exe)
    if resolved:
        return (resolved, args)
    
    return (exe, args)


# 导出
__all__ = [
    "find_executable",
]
