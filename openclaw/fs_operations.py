"""
FsOperations - 文件系统操作
基于 Claude Code fs_operations.ts 设计

文件系统操作工具。
"""
import os
import shutil
from typing import List, Optional


def exists(path: str) -> bool:
    """检查路径是否存在"""
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


def read(path: str) -> bytes:
    """读取文件"""
    with open(path, 'rb') as f:
        return f.read()


def read_text(path: str, encoding: str = 'utf-8') -> str:
    """读取文本文件"""
    with open(path, 'r', encoding=encoding) as f:
        return f.read()


def write(path: str, content: bytes):
    """写入文件"""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)


def write_text(path: str, content: str, encoding: str = 'utf-8'):
    """写入文本文件"""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)


def append(path: str, content: bytes):
    """追加内容"""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'ab') as f:
        f.write(content)


def append_text(path: str, content: str, encoding: str = 'utf-8'):
    """追加文本"""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'a', encoding=encoding) as f:
        f.write(content)


def remove(path: str):
    """删除文件或目录"""
    if is_dir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def copy(from_path: str, to_path: str):
    """复制文件或目录"""
    os.makedirs(os.path.dirname(to_path) or '.', exist_ok=True)
    if is_dir(from_path):
        shutil.copytree(from_path, to_path)
    else:
        shutil.copy2(from_path, to_path)


def move(from_path: str, to_path: str):
    """移动文件或目录"""
    os.makedirs(os.path.dirname(to_path) or '.', exist_ok=True)
    shutil.move(from_path, to_path)


def mkdir(path: str, parents: bool = True):
    """创建目录"""
    os.makedirs(path, exist_ok=parents)


def list_dir(path: str) -> List[str]:
    """列出目录内容"""
    return os.listdir(path)


def size(path: str) -> int:
    """获取文件大小"""
    return os.path.getsize(path)


def modified_time(path: str) -> float:
    """获取修改时间"""
    return os.path.getmtime(path)


def created_time(path: str) -> float:
    """获取创建时间"""
    return os.path.getctime(path)


def walk(top: str, topdown: bool = True) -> List[tuple]:
    """
    遍历目录
    
    Returns:
        [(dirpath, dirnames, filenames)]
    """
    import os
    results = []
    for dirpath, dirnames, filenames in os.walk(top, topdown=topdown):
        results.append((dirpath, dirnames, filenames))
    return results


def find(top: str, pattern: str = None) -> List[str]:
    """
    查找文件
    
    Args:
        top: 起始目录
        pattern: 文件名模式
    """
    import fnmatch
    results = []
    for dirpath, _, filenames in walk(top):
        for name in filenames:
            if pattern is None or fnmatch.fnmatch(name, pattern):
                results.append(os.path.join(dirpath, name))
    return results


# 导出
__all__ = [
    "exists",
    "is_file",
    "is_dir",
    "is_link",
    "read",
    "read_text",
    "write",
    "write_text",
    "append",
    "append_text",
    "remove",
    "copy",
    "move",
    "mkdir",
    "list_dir",
    "size",
    "modified_time",
    "created_time",
    "walk",
    "find",
]
