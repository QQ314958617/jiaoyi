"""
Path - 路径工具
基于 Claude Code path.ts 设计

路径处理工具。
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
    return os.path.join(*paths)


def dirname(path: str) -> str:
    """获取目录名"""
    return os.path.dirname(path)


def basename(path: str, ext: str = None) -> str:
    """
    获取文件名
    
    Args:
        path: 完整路径
        ext: 要去除的扩展名
    """
    b = os.path.basename(path)
    if ext and b.endswith(ext):
        return b[:-len(ext)]
    return b


def extname(path: str) -> str:
    """获取扩展名"""
    _, ext = os.path.splitext(path)
    return ext


def resolve(*paths: str) -> str:
    """
    解析为绝对路径
    
    Args:
        *paths: 路径片段
        
    Returns:
        绝对路径
    """
    return os.path.abspath(join(*paths))


def relative(from_path: str, to_path: str) -> str:
    """获取相对路径"""
    return os.path.relpath(from_path, to_path)


def is_absolute(path: str) -> bool:
    """是否为绝对路径"""
    return os.path.isabs(path)


def normalize(path: str) -> str:
    """规范化路径"""
    return os.path.normpath(path)


def split(path: str) -> List[str]:
    """分割路径为目录列表"""
    parts = []
    while True:
        path, tail = os.path.split(path)
        if tail:
            parts.insert(0, tail)
        else:
            if path:
                parts.insert(0, path)
            break
    return parts


def common_prefix(paths: List[str]) -> str:
    """获取公共前缀"""
    if not paths:
        return ''
    
    parts = [split(p) for p in paths]
    common = []
    
    for parts_tuple in zip(*parts):
        if len(set(parts_tuple)) == 1:
            common.append(parts_tuple[0])
        else:
            break
    
    return join(*common) if common else ''


def with_ext(path: str, ext: str) -> str:
    """替换扩展名"""
    if not ext.startswith('.'):
        ext = '.' + ext
    
    return os.path.splitext(path)[0] + ext


def without_ext(path: str) -> str:
    """去除扩展名"""
    return os.path.splitext(path)[0]


def change_ext(path: str, new_ext: str) -> str:
    """更改扩展名"""
    return with_ext(path, new_ext)


def split_ext(path: str) -> tuple:
    """分割为(无扩展名路径, 扩展名)"""
    return os.path.splitext(path)


def is_subpath(parent: str, child: str) -> bool:
    """检查是否为子路径"""
    parent = normalize(parent)
    child = normalize(child)
    return child.startswith(parent)


def make_relative(path: str, base: str) -> str:
    """转为相对路径"""
    return os.path.relpath(path, base)


# Path对象封装
class PathObj:
    """路径对象封装"""
    
    def __init__(self, path: str):
        self._path = Path(path)
    
    @property
    def path(self) -> str:
        return str(self._path)
    
    @property
    def name(self) -> str:
        return self._path.name
    
    @property
    def stem(self) -> str:
        return self._path.stem
    
    @property
    def ext(self) -> str:
        return self._path.suffix
    
    @property
    def parent(self) -> str:
        return str(self._path.parent)
    
    def exists(self) -> bool:
        return self._path.exists()
    
    def is_file(self) -> bool:
        return self._path.is_file()
    
    def is_dir(self) -> bool:
        return self._path.is_dir()
    
    def read_text(self, encoding: str = 'utf-8') -> str:
        return self._path.read_text(encoding=encoding)
    
    def write_text(self, content: str, encoding: str = 'utf-8') -> None:
        self._path.write_text(content, encoding=encoding)
    
    def iterdir(self):
        return self._path.iterdir()
    
    def glob(self, pattern: str):
        return self._path.glob(pattern)


# 导出
__all__ = [
    "join",
    "dirname",
    "basename",
    "extname",
    "resolve",
    "relative",
    "is_absolute",
    "normalize",
    "split",
    "common_prefix",
    "with_ext",
    "without_ext",
    "change_ext",
    "split_ext",
    "is_subpath",
    "make_relative",
    "PathObj",
]
