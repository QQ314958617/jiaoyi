"""
OpenClaw XDG Base Directory
=========================
Inspired by Claude Code's src/utils/xdg.ts.

XDG Base Directory 规范实现，支持：
1. XDG 目录获取
2. 默认值处理
3. 环境变量覆盖
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# ============================================================================
# XDG 目录
# ============================================================================

def get_home() -> str:
    """获取用户主目录"""
    return str(Path.home())

def get_xdg_state_home(env: Optional[dict] = None) -> str:
    """
    获取 XDG_STATE_HOME 目录
    
    默认值: ~/.local/state
    
    用于存放用户状态文件（如 lastpass, ssh 密钥等）
    """
    if env is None:
        env = os.environ
    
    if "XDG_STATE_HOME" in env:
        return env["XDG_STATE_HOME"]
    
    return os.path.join(get_home(), ".local", "state")

def get_xdg_cache_home(env: Optional[dict] = None) -> str:
    """
    获取 XDG_CACHE_HOME 目录
    
    默认值: ~/.cache
    
    用于存放缓存文件
    """
    if env is None:
        env = os.environ
    
    if "XDG_CACHE_HOME" in env:
        return env["XDG_CACHE_HOME"]
    
    return os.path.join(get_home(), ".cache")

def get_xdg_data_home(env: Optional[dict] = None) -> str:
    """
    获取 XDG_DATA_HOME 目录
    
    默认值: ~/.local/share
    
    用于存放数据文件
    """
    if env is None:
        env = os.environ
    
    if "XDG_DATA_HOME" in env:
        return env["XDG_DATA_HOME"]
    
    return os.path.join(get_home(), ".local", "share")

def get_xdg_config_home(env: Optional[dict] = None) -> str:
    """
    获取 XDG_CONFIG_HOME 目录
    
    默认值: ~/.config
    
    用于存放配置文件
    """
    if env is None:
        env = os.environ
    
    if "XDG_CONFIG_HOME" in env:
        return env["XDG_CONFIG_HOME"]
    
    return os.path.join(get_home(), ".config")

def get_xdg_runtime_dir(env: Optional[dict] = None) -> Optional[str]:
    """
    获取 XDG_RUNTIME_DIR 目录
    
    默认值: None (运行时生成)
    
    用于存放运行时文件（如 socket, pid 文件等）
    """
    if env is None:
        env = os.environ
    
    if "XDG_RUNTIME_DIR" in env:
        return env["XDG_RUNTIME_DIR"]
    
    # 尝试生成默认值
    # 通常是 /run/user/{uid} 或 /tmp/xdg-runtime-{uid}
    import pwd
    uid = pwd.getpwuid(os.getuid()).pw_uid
    default = f"/run/user/{uid}"
    if os.path.isdir(default):
        return default
    
    return None

def get_user_bin_dir(env: Optional[dict] = None) -> str:
    """
    获取用户 bin 目录
    
    默认值: ~/.local/bin
    
    用户安装的可执行文件放在这里
    """
    if env is None:
        env = os.environ
    
    # 检查 USE_LOCAL_BIN 环境变量
    if "USE_LOCAL_BIN" in env:
        return env["USE_LOCAL_BIN"]
    
    return os.path.join(get_home(), ".local", "bin")

# ============================================================================
# XDG 目录树
# ============================================================================

def ensure_xdg_dirs() -> dict:
    """
    确保所有 XDG 目录存在
    
    Returns:
        各目录路径的字典
    """
    dirs = {}
    
    # 确保主要目录存在
    for name, path_func in [
        ("config", get_xdg_config_home),
        ("data", get_xdg_data_home),
        ("cache", get_xdg_cache_home),
        ("state", get_xdg_state_home),
        ("bin", get_user_bin_dir),
    ]:
        path = path_func()
        os.makedirs(path, exist_ok=True)
        dirs[name] = path
    
    # runtime 可能不存在
    runtime = get_xdg_runtime_dir()
    if runtime:
        os.makedirs(runtime, exist_ok=True)
        dirs["runtime"] = runtime
    
    return dirs

# ============================================================================
# 便捷函数
# ============================================================================

def get_config_dir(subdir: str = "") -> str:
    """
    获取配置目录
    
    Args:
        subdir: 子目录（会自动创建）
    """
    base = get_xdg_config_home()
    if subdir:
        path = os.path.join(base, subdir)
        os.makedirs(path, exist_ok=True)
        return path
    return base

def get_data_dir(subdir: str = "") -> str:
    """获取数据目录"""
    base = get_xdg_data_home()
    if subdir:
        path = os.path.join(base, subdir)
        os.makedirs(path, exist_ok=True)
        return path
    return base

def get_cache_dir(subdir: str = "") -> str:
    """获取缓存目录"""
    base = get_xdg_cache_home()
    if subdir:
        path = os.path.join(base, subdir)
        os.makedirs(path, exist_ok=True)
        return path
    return base

def get_state_dir(subdir: str = "") -> str:
    """获取状态目录"""
    base = get_xdg_state_home()
    if subdir:
        path = os.path.join(base, subdir)
        os.makedirs(path, exist_ok=True)
        return path
    return base

# ============================================================================
# 路径组合
# ============================================================================

def config_path(*parts: str) -> str:
    """获取配置目录下的路径"""
    return os.path.join(get_xdg_config_home(), *parts)

def data_path(*parts: str) -> str:
    """获取数据目录下的路径"""
    return os.path.join(get_xdg_data_home(), *parts)

def cache_path(*parts: str) -> str:
    """获取缓存目录下的路径"""
    return os.path.join(get_xdg_cache_home(), *parts)

def state_path(*parts: str) -> str:
    """获取状态目录下的路径"""
    return os.path.join(get_xdg_state_home(), *parts)
