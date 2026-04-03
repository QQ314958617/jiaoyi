"""
OpenClaw Path Utilities
====================
Inspired by Claude Code's src/utils/path.ts.

路径工具，支持：
1. 路径展开（~、相对路径）
2. 路径规范化
3. 路径安全检查
4. 跨平台路径处理
"""

from __future__ import annotations

import os, pathlib
from pathlib import Path
from typing import Optional, Union

# ============================================================================
# 路径展开
# ============================================================================

def expand_path(path: str, base_dir: Optional[str] = None) -> str:
    """
    展开路径
    
    支持：
    - ~ 展开为用户目录
    - 相对路径基于 base_dir 解析
    - 绝对路径直接返回
    
    Args:
        path: 路径（可能包含 ~ 或相对路径）
        base_dir: 基础目录，默认为当前工作目录
    
    Returns:
        展开后的绝对路径
    """
    if not path:
        return os.path.abspath(base_dir or ".")
    
    # 检查空字节
    if '\0' in path:
        raise ValueError("Path contains null bytes")
    
    path = path.strip()
    
    if not path or path == "~":
        return str(Path.home())
    
    # ~ 展开
    if path.startswith("~/"):
        path = str(Path.home() / path[2:])
    elif path == "~":
        return str(Path.home())
    
    # 相对路径
    if not os.path.isabs(path):
        if base_dir:
            path = os.path.join(base_dir, path)
        else:
            path = os.path.abspath(path)
    
    return os.path.normpath(path)


def expand_paths(paths: list[str], base_dir: Optional[str] = None) -> list[str]:
    """批量展开路径"""
    return [expand_path(p, base_dir) for p in paths]


# ============================================================================
# 路径规范化
# ============================================================================

def normalize_path(path: str) -> str:
    """规范化路径"""
    return os.path.normpath(os.path.abspath(path))


def relpath(path: str, start: Optional[str] = None) -> str:
    """获取相对路径"""
    if start is None:
        start = os.getcwd()
    return os.path.relpath(path, start)


def common_prefix(paths: list[str]) -> str:
    """获取公共前缀路径"""
    if not paths:
        return ""
    
    parts_list = [p.split(os.sep) for p in paths]
    
    common = []
    for parts in zip(*parts_list):
        if len(set(parts)) == 1:
            common.append(parts[0])
        else:
            break
    
    return os.sep.join(common) if common else ""


def ensure_dir(path: str) -> str:
    """确保目录存在（返回路径）"""
    os.makedirs(path, exist_ok=True)
    return path


# ============================================================================
# 路径安全检查
# ============================================================================

def is_subpath(path: str, parent: str) -> bool:
    """检查 path 是否是 parent 的子路径"""
    path = os.path.abspath(path)
    parent = os.path.abspath(parent)
    return path.startswith(parent + os.sep) or path == parent


def is_safe_path(path: str, allowed_dirs: list[str]) -> bool:
    """
    检查路径是否在允许的目录内
    
    Args:
        path: 要检查的路径
        allowed_dirs: 允许的目录列表
    
    Returns:
        True if path is within any allowed_dir
    """
    path = os.path.abspath(path)
    for allowed in allowed_dirs:
        allowed = os.path.abspath(allowed)
        if is_subpath(path, allowed):
            return True
    return False


def safe_join(base: str, *parts: str) -> str:
    """
    安全拼接路径，防止路径遍历攻击
    
    Example:
        safe_join("/data", "..", "secret") → "/data/secret" (不允许)
    """
    result = os.path.abspath(os.path.join(base, *parts))
    
    # 确保结果在 base 目录内
    if not result.startswith(os.path.abspath(base) + os.sep):
        if result != os.path.abspath(base):
            raise ValueError(f"Path traversal attempt detected: {parts}")
    
    return result


# ============================================================================
# 文件名和扩展名
# ============================================================================

def get_basename(path: str) -> str:
    """获取文件名（不含扩展名）"""
    return os.path.splitext(os.path.basename(path))[0]


def get_extension(path: str) -> str:
    """获取扩展名（包含点）"""
    return os.path.splitext(path)[1]


def change_extension(path: str, new_ext: str) -> str:
    """更换扩展名"""
    base = os.path.splitext(path)[0]
    if not new_ext.startswith('.'):
        new_ext = '.' + new_ext
    return base + new_ext


def split_extension(path: str) -> tuple[str, str]:
    """分离文件名和扩展名"""
    base, ext = os.path.splitext(path)
    return base, ext


# ============================================================================
# 路径比较
# ============================================================================

def same_file(path1: str, path2: str) -> bool:
    """检查两个路径是否指向同一文件"""
    try:
        return os.path.samefile(path1, path2)
    except OSError:
        return os.path.abspath(path1) == os.path.abspath(path2)


def is_hidden(path: str) -> bool:
    """检查路径是否隐藏（Unix 风格）"""
    basename = os.path.basename(path)
    return basename.startswith('.')


def is_directory(path: str) -> bool:
    """检查是否是目录"""
    return os.path.isdir(path)


def is_file(path: str) -> bool:
    """检查是否是文件"""
    return os.path.isfile(path)


def exists(path: str) -> bool:
    """检查路径是否存在"""
    return os.path.exists(path)


# ============================================================================
# 临时文件
# ============================================================================

import tempfile

def temp_dir(suffix: Optional[str] = None, prefix: Optional[str] = None) -> str:
    """创建临时目录"""
    return tempfile.mkdtemp(suffix=suffix, prefix=prefix)


def temp_file(suffix: Optional[str] = None, prefix: Optional[str] = None) -> str:
    """创建临时文件"""
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return path


# ============================================================================
# 路径转换
# ============================================================================

def to_posix_path(path: str) -> str:
    """转换为 POSIX 风格路径（正斜杠）"""
    return path.replace('\\', '/')


def to_windows_path(path: str) -> str:
    """转换为 Windows 风格路径（反斜杠）"""
    return path.replace('/', '\\')


def native_path(path: str) -> str:
    """转换为原生路径风格"""
    return os.path.normpath(path)


# ============================================================================
# 大小和距离
# ============================================================================

def distance_to(path1: str, path2: str) -> int:
    """
    计算两个路径的距离（目录层级差）
    
    Example:
        distance("/a/b/c", "/a/b") → 1
        distance("/a/b", "/a/b/c") → 1
    """
    p1 = os.path.abspath(path1).split(os.sep)
    p2 = os.path.abspath(path2).split(os.sep)
    
    # 找到公共前缀
    common_len = 0
    for a, b in zip(p1, p2):
        if a == b:
            common_len += 1
        else:
            break
    
    # 距离 = (p1长度 - 公共前缀) + (p2长度 - 公共前缀)
    return (len(p1) - common_len) + (len(p2) - common_len)
