"""
IdePathConversion - IDE路径转换
基于 Claude Code ide_path_conversion.ts 设计

IDE路径转换工具。
"""
import os
import platform


def to_uri(path: str) -> str:
    """
    路径转URI
    
    Args:
        path: 文件路径
        
    Returns:
        file:// URI
    """
    if platform.system() == "Windows":
        # Windows: C:\path -> file:///C:/path
        path = path.replace("\\", "/")
        return f"file:///{path}"
    else:
        # Unix: /path -> file:///path
        return f"file://{path}"


def from_uri(uri: str) -> str:
    """
    URI转路径
    
    Args:
        uri: file:// URI
        
    Returns:
        文件路径
    """
    if uri.startswith("file://"):
        path = uri[7:]
        # 移除开头的/
        if path.startswith("/"):
            path = path[1:]
        if platform.system() == "Windows":
            path = path.replace("/", "\\")
        return path
    return uri


def to_vscode(path: str, line: int = None) -> str:
    """
    转换为VSCode URL
    
    Args:
        path: 文件路径
        line: 行号
    """
    uri = to_uri(path)
    if line:
        return f"vscode://file/{uri}:{line}"
    return f"vscode://file/{uri}"


def to_jetbrains(path: str, line: int = None) -> str:
    """
    转换为JetBrains URL
    
    Args:
        path: 文件路径
        line: 行号
    """
    if line:
        return f"jetbrains://vscode/file/{path}:{line}"
    return f"jetbrains://vscode/file/{path}"


def to_vim(path: str, line: int = None) -> str:
    """
    转换为Vim命令
    
    Args:
        path: 文件路径
        line: 行号
    """
    if line:
        return f"+{line} {path}"
    return path


def is_windows() -> bool:
    """是否为Windows"""
    return platform.system() == "Windows"


def is_mac() -> bool:
    """是否为macOS"""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """是否为Linux"""
    return platform.system() == "Linux"


def normalize_path(path: str) -> str:
    """规范化路径"""
    return os.path.normpath(path)


# 导出
__all__ = [
    "to_uri",
    "from_uri",
    "to_vscode",
    "to_jetbrains",
    "to_vim",
    "is_windows",
    "is_mac",
    "is_linux",
    "normalize_path",
]
