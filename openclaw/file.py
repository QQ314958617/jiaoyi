"""
File - 文件
基于 Claude Code file.ts 设计

文件工具。
"""
import os
from typing import List


def exists(path: str) -> bool:
    """是否存在"""
    return os.path.exists(path)


def is_file(path: str) -> bool:
    """是否为文件"""
    return os.path.isfile(path)


def is_dir(path: str) -> bool:
    """是否为目录"""
    return os.path.isdir(path)


def is_link(path: str) -> bool:
    """是否为链接"""
    return os.path.islink(path)


def size(path: str) -> int:
    """文件大小"""
    return os.path.getsize(path)


def read_file(path: str) -> bytes:
    """读取文件"""
    with open(path, 'rb') as f:
        return f.read()


def write_file(path: str, content: bytes) -> None:
    """写入文件"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)


def read_text(path: str, encoding: str = 'utf-8') -> str:
    """读取文本文件"""
    with open(path, 'r', encoding=encoding) as f:
        return f.read()


def write_text(path: str, text: str, encoding: str = 'utf-8') -> None:
    """写入文本文件"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding=encoding) as f:
        f.write(text)


def append_text(path: str, text: str, encoding: str = 'utf-8') -> None:
    """追加文本"""
    with open(path, 'a', encoding=encoding) as f:
        f.write(text)


def list_dir(path: str) -> List[str]:
    """列出目录"""
    return os.listdir(path)


def make_dir(path: str) -> None:
    """创建目录"""
    os.makedirs(path, exist_ok=True)


def remove_file(path: str) -> None:
    """删除文件"""
    os.remove(path)


def remove_dir(path: str) -> None:
    """删除目录"""
    os.rmdir(path)


def copy_file(from_path: str, to_path: str) -> None:
    """复制文件"""
    import shutil
    os.makedirs(os.path.dirname(to_path), exist_ok=True)
    shutil.copy2(from_path, to_path)


def move_file(from_path: str, to_path: str) -> None:
    """移动文件"""
    import shutil
    os.makedirs(os.path.dirname(to_path), exist_ok=True)
    shutil.move(from_path, to_path)


# 导出
__all__ = [
    "exists",
    "is_file",
    "is_dir",
    "is_link",
    "size",
    "read_file",
    "write_file",
    "read_text",
    "write_text",
    "append_text",
    "list_dir",
    "make_dir",
    "remove_file",
    "remove_dir",
    "copy_file",
    "move_file",
]
