"""
Path - 路径
基于 Claude Code path.ts 设计

路径工具。
"""
import os
from typing import List


def basename(path: str) -> str:
    """文件名"""
    return os.path.basename(path)


def dirname(path: str) -> str:
    """目录名"""
    return os.path.dirname(path)


def extname(path: str) -> str:
    """扩展名"""
    return os.path.splitext(path)[1]


def join(*paths: str) -> str:
    """拼接路径"""
    return os.path.join(*paths)


def resolve(*paths: str) -> str:
    """解析为绝对路径"""
    return os.path.abspath(os.path.join(*paths))


def normalize(path: str) -> str:
    """规范化路径"""
    return os.path.normpath(path)


def is_absolute(path: str) -> bool:
    """是否为绝对路径"""
    return os.path.isabs(path)


def is_relative(path: str) -> bool:
    """是否为相对路径"""
    return not os.path.isabs(path)


def relative(from_path: str, to_path: str) -> str:
    """相对路径"""
    return os.path.relpath(to_path, from_path)


def split(path: str) -> List[str]:
    """分割路径为目录列表"""
    parts = []
    while True:
        path, part = os.path.split(path)
        if part:
            parts.insert(0, part)
        else:
            if path:
                parts.insert(0, path)
            break
    return parts


def extname_without_dot(path: str) -> str:
    """扩展名（不带点）"""
    ext = extname(path)
    return ext[1:] if ext.startswith('.') else ext


def change_ext(path: str, new_ext: str) -> str:
    """更换扩展名"""
    base = os.path.splitext(path)[0]
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    return base + new_ext


def join_ext(path: str, ext: str) -> str:
    """添加扩展名"""
    if not ext.startswith('.'):
        ext = '.' + ext
    return path + ext


# 导出
__all__ = [
    "basename",
    "dirname",
    "extname",
    "join",
    "resolve",
    "normalize",
    "is_absolute",
    "is_relative",
    "relative",
    "split",
    "extname_without_dot",
    "change_ext",
    "join_ext",
]
