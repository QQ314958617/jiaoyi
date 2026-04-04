"""
Temp - 临时文件
基于 Claude Code temp.ts 设计

临时文件工具。
"""
import os
import tempfile
import uuid


def mktemp(suffix: str = "", prefix: str = "tmp") -> str:
    """
    创建临时文件
    
    Returns:
        文件路径
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return path


def mktemp_dir(suffix: str = "", prefix: str = "tmp") -> str:
    """
    创建临时目录
    
    Returns:
        目录路径
    """
    return tempfile.mkdtemp(suffix=suffix, prefix=prefix)


def temp_dir() -> str:
    """系统临时目录"""
    return tempfile.gettempdir()


def temp_file() -> str:
    """临时文件路径"""
    return mktemp()


def with_temp_file(fn: callable, suffix: str = "", prefix: str = "tmp") -> any:
    """
    使用临时文件（自动清理）
    
    Args:
        fn: 接收文件路径的函数
    """
    path = mktemp(suffix=suffix, prefix=prefix)
    try:
        return fn(path)
    finally:
        if os.path.exists(path):
            os.remove(path)


def with_temp_dir(fn: callable, suffix: str = "", prefix: str = "tmp") -> any:
    """
    使用临时目录（自动清理）
    
    Args:
        fn: 接收目录路径的函数
    """
    path = mktemp_dir(suffix=suffix, prefix=prefix)
    try:
        return fn(path)
    finally:
        import shutil
        if os.path.exists(path):
            shutil.rmtree(path)


def unique_name(prefix: str = "") -> str:
    """生成唯一名称"""
    uid = uuid.uuid4().hex[:8]
    return f"{prefix}{uid}" if prefix else uid


# 导出
__all__ = [
    "mktemp",
    "mktemp_dir",
    "temp_dir",
    "temp_file",
    "with_temp_file",
    "with_temp_dir",
    "unique_name",
]
