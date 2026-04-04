"""
File - 文件工具
基于 Claude Code file.ts 设计

文件处理工具。
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional


def read_file(path: str, encoding: str = 'utf-8') -> str:
    """
    读取文件
    
    Args:
        path: 文件路径
        encoding: 编码
        
    Returns:
        文件内容
    """
    with open(path, 'r', encoding=encoding) as f:
        return f.read()


def write_file(path: str, content: str, encoding: str = 'utf-8') -> None:
    """
    写入文件
    
    Args:
        path: 文件路径
        content: 内容
        encoding: 编码
    """
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)


def read_lines(path: str, encoding: str = 'utf-8') -> List[str]:
    """读取所有行"""
    with open(path, 'r', encoding=encoding) as f:
        return f.readlines()


def write_lines(path: str, lines: List[str], encoding: str = 'utf-8') -> None:
    """写入多行"""
    with open(path, 'w', encoding=encoding) as f:
        f.writelines(lines)


def append_file(path: str, content: str, encoding: str = 'utf-8') -> None:
    """追加内容"""
    with open(path, 'a', encoding=encoding) as f:
        f.write(content)


def exists(path: str) -> bool:
    """检查文件是否存在"""
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


def get_size(path: str) -> int:
    """获取文件大小（字节）"""
    return os.path.getsize(path)


def get_mtime(path: str) -> float:
    """获取修改时间"""
    return os.path.getmtime(path)


def get_ctime(path: str) -> float:
    """获取创建时间"""
    return os.path.getctime(path)


def list_files(
    path: str,
    pattern: str = None,
    recursive: bool = False,
) -> List[str]:
    """
    列出文件
    
    Args:
        path: 目录路径
        pattern: 文件名模式
        recursive: 是否递归
        
    Returns:
        文件路径列表
    """
    import fnmatch
    
    results = []
    
    if recursive:
        for root, dirs, files in os.walk(path):
            for name in files:
                if pattern is None or fnmatch.fnmatch(name, pattern):
                    results.append(os.path.join(root, name))
    else:
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            if os.path.isfile(full_path):
                if pattern is None or fnmatch.fnmatch(name, pattern):
                    results.append(full_path)
    
    return results


def list_dirs(path: str, recursive: bool = False) -> List[str]:
    """列出子目录"""
    results = []
    
    if recursive:
        for root, dirs, files in os.walk(path):
            for name in dirs:
                results.append(os.path.join(root, name))
    else:
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                results.append(full_path)
    
    return results


def make_dir(path: str, parents: bool = True) -> None:
    """创建目录"""
    os.makedirs(path, exist_ok=True)


def remove_file(path: str) -> None:
    """删除文件"""
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)


def remove_dir(path: str) -> None:
    """删除目录"""
    if os.path.isdir(path):
        shutil.rmtree(path)


def copy_file(src: str, dst: str) -> None:
    """复制文件"""
    shutil.copy2(src, dst)


def copy_dir(src: str, dst: str) -> None:
    """复制目录"""
    shutil.copytree(src, dst)


def move(src: str, dst: str) -> None:
    """移动文件/目录"""
    shutil.move(src, dst)


def get_temp_file(suffix: str = '') -> str:
    """获取临时文件路径"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return path


def get_temp_dir() -> str:
    """获取临时目录路径"""
    return tempfile.mkdtemp()


class FileWatcher:
    """文件监视器"""
    
    def __init__(self, path: str, callback: Callable):
        self._path = path
        self._callback = callback
        self._mtime = None
    
    def check(self) -> bool:
        """检查是否变化"""
        if not exists(self._path):
            return False
        
        current_mtime = get_mtime(self._path)
        
        if self._mtime is None:
            self._mtime = current_mtime
            return False
        
        if current_mtime != self._mtime:
            self._mtime = current_mtime
            self._callback(self._path)
            return True
        
        return False


# 导出
__all__ = [
    "read_file",
    "write_file",
    "read_lines",
    "write_lines",
    "append_file",
    "exists",
    "is_file",
    "is_dir",
    "is_link",
    "get_size",
    "get_mtime",
    "get_ctime",
    "list_files",
    "list_dirs",
    "make_dir",
    "remove_file",
    "remove_dir",
    "copy_file",
    "copy_dir",
    "move",
    "get_temp_file",
    "get_temp_dir",
    "FileWatcher",
]
