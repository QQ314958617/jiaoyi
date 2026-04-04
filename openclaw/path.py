"""
Path - 路径
基于 Claude Code path.ts 设计

路径操作工具。
"""
import os
from pathlib import Path
from typing import List


def join(*paths: str) -> str:
    """
    连接路径
    
    Args:
        *paths: 路径片段
        
    Returns:
        连接后的路径
    """
    return str(Path(*paths))


def dirname(path: str) -> str:
    """获取目录名"""
    return str(Path(path).parent)


def basename(path: str) -> str:
    """获取文件名"""
    return Path(path).name


def extname(path: str) -> str:
    """获取扩展名（含点）"""
    return Path(path).suffix


def stem(path: str) -> str:
    """获取文件名（不含扩展名）"""
    return Path(path).stem


def resolve(*paths: str) -> str:
    """
    解析为绝对路径
    
    Args:
        *paths: 路径
        
    Returns:
        绝对路径
    """
    return str(Path(*paths).resolve())


def relative(from_path: str, to: str) -> str:
    """
    计算相对路径
    
    Args:
        from_path: 起始路径
        to: 目标路径
        
    Returns:
        相对路径
    """
    return str(Path(from_path).relative_to(to))


def normalize(path: str) -> str:
    """规范化路径"""
    return str(Path(path).resolve())


def is_absolute(path: str) -> bool:
    """是否为绝对路径"""
    return Path(path).is_absolute()


def is_relative(path: str) -> bool:
    """是否为相对路径"""
    return not Path(path).is_absolute()


def split(path: str) -> List[str]:
    """分割路径为各部分"""
    return list(Path(path).parts)


def with_ext(path: str, ext: str) -> str:
    """
    替换扩展名
    
    Args:
        path: 路径
        ext: 新扩展名（可含点或不含）
        
    Returns:
        新路径
    """
    p = Path(path)
    if not ext.startswith('.'):
        ext = '.' + ext
    return str(p.with_suffix(ext))


def without_ext(path: str) -> str:
    """移除扩展名"""
    return str(Path(path).with_suffix(''))
