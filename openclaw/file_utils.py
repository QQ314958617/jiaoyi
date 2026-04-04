"""
File Utilities - 文件工具
基于 Claude Code file.ts 设计

文件操作常用工具。
"""
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


MAX_OUTPUT_SIZE = 0.25 * 1024 * 1024  # 0.25MB


@dataclass
class File:
    """文件对象"""
    filename: str
    content: str


def path_exists(path: str) -> bool:
    """
    检查路径是否存在
    
    Args:
        path: 路径
        
    Returns:
        是否存在
    """
    return os.path.exists(path)


def read_file_safe(filepath: str) -> Optional[str]:
    """
    安全读取文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        文件内容或None
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def get_file_modification_time(filepath: str) -> float:
    """
    获取文件修改时间（毫秒）
    
    Args:
        filepath: 文件路径
        
    Returns:
        修改时间戳
    """
    return os.path.getmtime(filepath)


def get_file_size(filepath: str) -> int:
    """
    获取文件大小（字节）
    
    Args:
        filepath: 文件路径
        
    Returns:
        文件大小
    """
    return os.path.getsize(filepath)


def get_filename(filepath: str) -> str:
    """
    获取文件名
    
    Args:
        filepath: 文件路径
        
    Returns:
        文件名
    """
    return os.path.basename(filepath)


def get_extension(filepath: str) -> str:
    """
    获取文件扩展名
    
    Args:
        filepath: 文件路径
        
    Returns:
        扩展名（包含.）
    """
    return os.path.splitext(filepath)[1]


def get_directory(filepath: str) -> str:
    """
    获取文件所在目录
    
    Args:
        filepath: 文件路径
        
    Returns:
        目录路径
    """
    return os.path.dirname(filepath)


def is_absolute(filepath: str) -> bool:
    """
    检查是否为绝对路径
    
    Args:
        filepath: 路径
        
    Returns:
        是否为绝对路径
    """
    return os.path.isabs(filepath)


def join_path(*parts: str) -> str:
    """
    连接路径
    
    Returns:
        连接后的路径
    """
    return os.path.join(*parts)


def normalize_path(filepath: str) -> str:
    """
    规范化路径
    
    Args:
        filepath: 路径
        
    Returns:
        规范化后的路径
    """
    return os.path.normpath(filepath)


def get_relative_path(filepath: str, base: str) -> str:
    """
    获取相对路径
    
    Args:
        filepath: 文件路径
        base: 基准路径
        
    Returns:
        相对路径
    """
    return os.path.relpath(filepath, base)


def resolve_path(filepath: str) -> str:
    """
    解析为绝对路径
    
    Args:
        filepath: 路径
        
    Returns:
        绝对路径
    """
    return os.path.abspath(filepath)


def ensure_directory(dirpath: str) -> None:
    """
    确保目录存在
    
    Args:
        dirpath: 目录路径
    """
    os.makedirs(dirpath, exist_ok=True)


def copy_file(src: str, dst: str) -> None:
    """
    复制文件
    
    Args:
        src: 源路径
        dst: 目标路径
    """
    shutil.copy2(src, dst)


def move_file(src: str, dst: str) -> None:
    """
    移动文件
    
    Args:
        src: 源路径
        dst: 目标路径
    """
    shutil.move(src, dst)


def delete_file(filepath: str) -> None:
    """
    删除文件
    
    Args:
        filepath: 文件路径
    """
    if os.path.exists(filepath):
        os.remove(filepath)


# 导出
__all__ = [
    "File",
    "MAX_OUTPUT_SIZE",
    "path_exists",
    "read_file_safe",
    "get_file_modification_time",
    "get_file_size",
    "get_filename",
    "get_extension",
    "get_directory",
    "is_absolute",
    "join_path",
    "normalize_path",
    "get_relative_path",
    "resolve_path",
    "ensure_directory",
    "copy_file",
    "move_file",
    "delete_file",
]
