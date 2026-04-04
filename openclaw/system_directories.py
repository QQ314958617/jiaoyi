"""
SystemDirectories - 系统目录
基于 Claude Code system_directories.ts 设计

系统目录工具。
"""
import os
import platform


def home() -> str:
    """用户主目录"""
    return os.path.expanduser("~")


def config() -> str:
    """配置目录"""
    if platform.system() == "Darwin":
        return os.path.join(home(), "Library", "Application Support")
    elif platform.system() == "Windows":
        return os.environ.get("APPDATA", os.path.join(home(), "AppData", "Roaming"))
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return xdg
        return os.path.join(home(), ".config")


def data() -> str:
    """数据目录"""
    if platform.system() == "Darwin":
        return os.path.join(home(), "Library", "Application Support")
    elif platform.system() == "Windows":
        return os.environ.get("LOCALAPPDATA", os.path.join(home(), "AppData", "Local"))
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        if xdg:
            return xdg
        return os.path.join(home(), ".local", "share")


def cache() -> str:
    """缓存目录"""
    if platform.system() == "Darwin":
        return os.path.join(home(), "Library", "Caches")
    elif platform.system() == "Windows":
        return os.environ.get("LOCALAPPDATA", os.path.join(home(), "AppData", "Local"))
    else:
        xdg = os.environ.get("XDG_CACHE_HOME")
        if xdg:
            return xdg
        return os.path.join(home(), ".cache")


def temp() -> str:
    """临时目录"""
    return os.environ.get("TMPDIR", "/tmp")


def desktop() -> str:
    """桌面目录"""
    if platform.system() == "Windows":
        return os.path.join(home(), "Desktop")
    elif platform.system() == "Darwin":
        return os.path.join(home(), "Desktop")
    else:
        return os.path.join(home(), "Desktop")


def documents() -> str:
    """文档目录"""
    if platform.system() == "Windows":
        return os.path.join(home(), "Documents")
    elif platform.system() == "Darwin":
        return os.path.join(home(), "Documents")
    else:
        return os.path.join(home(), "Documents")


def downloads() -> str:
    """下载目录"""
    if platform.system() == "Darwin":
        return os.path.join(home(), "Downloads")
    elif platform.system() == "Windows":
        return os.path.join(home(), "Downloads")
    else:
        return os.path.join(home(), "Downloads")


def project_dir() -> str:
    """项目目录"""
    return os.getcwd()


# 导出
__all__ = [
    "home",
    "config",
    "data",
    "cache",
    "temp",
    "desktop",
    "documents",
    "downloads",
    "project_dir",
]
