"""
FS - 文件系统
基于 Claude Code fs.ts 设计

文件系统工具。
"""
import os
import shutil
from pathlib import Path
from typing import Any, BinaryIO, List, Optional, TextIO


def exists(path: str) -> bool:
    """检查路径是否存在"""
    return Path(path).exists()


def is_file(path: str) -> bool:
    """是否为文件"""
    return Path(path).is_file()


def is_dir(path: str) -> bool:
    """是否为目录"""
    return Path(path).is_dir()


def is_link(path: str) -> bool:
    """是否为符号链接"""
    return Path(path).is_symlink()


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


def read_bytes(path: str) -> bytes:
    """读取二进制文件"""
    with open(path, 'rb') as f:
        return f.read()


def write_file(path: str, content: str, encoding: str = 'utf-8') -> None:
    """
    写入文件
    
    Args:
        path: 文件路径
        content: 内容
        encoding: 编码
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding=encoding) as f:
        f.write(content)


def write_bytes(path: str, content: bytes) -> None:
    """写入二进制文件"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)


def append_file(path: str, content: str, encoding: str = 'utf-8') -> None:
    """
    追加文件
    
    Args:
        path: 文件路径
        content: 内容
        encoding: 编码
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding=encoding) as f:
        f.write(content)


def delete(path: str) -> bool:
    """
    删除文件或目录
    
    Args:
        path: 路径
        
    Returns:
        是否成功
    """
    p = Path(path)
    if not p.exists():
        return False
    
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return True


def copy(src: str, dst: str) -> None:
    """
    复制文件或目录
    
    Args:
        src: 源路径
        dst: 目标路径
    """
    p_src = Path(src)
    p_dst = Path(dst)
    p_dst.parent.mkdir(parents=True, exist_ok=True)
    
    if p_src.is_dir():
        shutil.copytree(p_src, p_dst, dirs_exist_ok=True)
    else:
        shutil.copy2(p_src, p_dst)


def move(src: str, dst: str) -> None:
    """
    移动文件或目录
    
    Args:
        src: 源路径
        dst: 目标路径
    """
    p_src = Path(src)
    p_dst = Path(dst)
    p_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(p_src), str(p_dst))


def mkdir(path: str, parents: bool = True) -> None:
    """
    创建目录
    
    Args:
        path: 目录路径
        parents: 是否创建父目录
    """
    Path(path).mkdir(parents=parents, exist_ok=True)


def list_dir(path: str) -> List[str]:
    """
    列出目录内容
    
    Args:
        path: 目录路径
        
    Returns:
        文件/目录名列表
    """
    return [p.name for p in Path(path).iterdir()]


def walk(path: str) -> List[str]:
    """
    递归遍历目录
    
    Args:
        path: 目录路径
        
    Returns:
        所有文件路径
    """
    result = []
    for root, dirs, files in os.walk(path):
        for f in files:
            result.append(os.path.join(root, f))
    return result


def size(path: str) -> int:
    """
    获取文件大小
    
    Args:
        path: 文件路径
        
    Returns:
        字节数
    """
    return Path(path).stat().st_size


def modified(path: str) -> float:
    """获取文件修改时间"""
    return Path(path).stat().st_mtime


def absolute(path: str) -> str:
    """获取绝对路径"""
    return str(Path(path).resolve())


def relative(path: str, start: str = None) -> str:
    """获取相对路径"""
    return str(Path(path).relative_to(start or os.getcwd()))


# 导出
__all__ = [
    "exists",
    "is_file",
    "is_dir",
    "is_link",
    "read_file",
    "read_bytes",
    "write_file",
    "write_bytes",
    "append_file",
    "delete",
    "copy",
    "move",
    "mkdir",
    "list_dir",
    "walk",
    "size",
    "modified",
    "absolute",
    "relative",
]
