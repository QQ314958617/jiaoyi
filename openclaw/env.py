"""
OpenClaw Environment Utilities
============================
Inspired by Claude Code's src/utils/env.ts and envUtils.ts.

环境检测和配置工具，支持：
1. 平台检测（Linux/Darwin/Windows）
2. 路径配置（配置目录、数据目录）
3. 环境变量便捷访问
4. 网络检测
5. 互联网连接检测
"""

from __future__ import annotations

import os, platform, socket
from pathlib import Path
from typing import Optional
from functools import lru_cache

# ============================================================================
# 平台检测
# ============================================================================

PLATFORM = platform.system().lower()
IS_LINUX = PLATFORM == "linux"
IS_DARWIN = PLATFORM == "darwin"
IS_WINDOWS = PLATFORM == "windows"
IS_WSL = False

# 检测 WSL
if IS_LINUX:
    try:
        IS_WSL = Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists()
    except:
        pass

# ============================================================================
# 路径配置
# ============================================================================

def get_home_dir() -> str:
    """获取用户主目录"""
    return str(Path.home())

def get_config_dir() -> str:
    """获取配置目录"""
    # CLAUDE_CONFIG_DIR > ~/.claude > ~/.config/openclaw
    env_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if env_dir:
        return env_dir
    
    legacy = Path.home() / ".claude"
    if legacy.exists():
        return str(legacy)
    
    config_home = os.environ.get("XDG_CONFIG_HOME")
    if config_home:
        return os.path.join(config_home, "openclaw")
    
    return str(Path.home() / ".config" / "openclaw")

def get_data_dir() -> str:
    """获取数据目录"""
    env_dir = os.environ.get("CLAUDE_DATA_DIR")
    if env_dir:
        return env_dir
    
    data_home = os.environ.get("XDG_DATA_HOME")
    if data_home:
        return os.path.join(data_home, "openclaw")
    
    return str(Path.home() / ".local" / "share" / "openclaw")

def get_cache_dir() -> str:
    """获取缓存目录"""
    env_dir = os.environ.get("CLAUDE_CACHE_DIR")
    if env_dir:
        return env_dir
    
    cache_home = os.environ.get("XDG_CACHE_HOME")
    if cache_home:
        return os.path.join(cache_home, "openclaw")
    
    return str(Path.home() / ".cache" / "openclaw")

def get_log_dir() -> str:
    """获取日志目录"""
    return os.path.join(get_data_dir(), "logs")

def ensure_dirs() -> None:
    """确保必要目录存在"""
    for d in [get_config_dir(), get_data_dir(), get_cache_dir(), get_log_dir()]:
        os.makedirs(d, exist_ok=True)

# ============================================================================
# 环境变量便捷访问
# ============================================================================

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """获取环境变量"""
    return os.environ.get(key, default)

def get_env_bool(key: str, default: bool = False) -> bool:
    """获取布尔环境变量"""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")

def get_env_int(key: str, default: int = 0) -> int:
    """获取整数环境变量"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """获取浮点环境变量"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default

# ============================================================================
# 网络检测
# ============================================================================

def has_internet_access(timeout: float = 2.0) -> bool:
    """检测互联网连接"""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("1.1.1.1", 53))
        return True
    except:
        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except:
            return False

def is_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """检测端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def is_host_reachable(host: str, timeout: float = 2.0) -> bool:
    """检测主机是否可达"""
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname(host)
        return True
    except socket.gaierror:
        return False

# ============================================================================
# 系统信息
# ============================================================================

@lru_cache(maxsize=1)
def get_hostname() -> str:
    """获取主机名"""
    return socket.gethostname()

@lru_cache(maxsize=1)
def get_ip_address() -> str:
    """获取本机 IP 地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

@lru_cache(maxsize=1)
def get_cpu_count() -> int:
    """获取 CPU 核心数"""
    return os.cpu_count() or 1

@lru_cache(maxsize=1)
def get_memory_info() -> dict:
    """获取内存信息"""
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
        
        mem = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                val_str = value.strip().split()[0]
                try:
                    mem[key] = int(val_str) // 1024  # KB to MB
                except:
                    pass
        
        return {
            "total": mem.get("MemTotal", 0),
            "available": mem.get("MemAvailable", 0),
            "used": mem.get("MemTotal", 0) - mem.get("MemAvailable", 0)
        }
    except:
        return {"total": 0, "available": 0, "used": 0}

# ============================================================================
# 可执行文件检测
# ============================================================================

def find_executable(name: str) -> Optional[str]:
    """查找可执行文件路径"""
    path_env = os.environ.get("PATH", os.defpath)
    
    for directory in path_env.split(os.pathsep):
        full_path = os.path.join(directory, name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
        
        # Windows 尝试 .exe 后缀
        if IS_WINDOWS:
            full_path_exe = full_path + ".exe"
            if os.path.isfile(full_path_exe) and os.access(full_path_exe, os.X_OK):
                return full_path_exe
    
    return None

def is_executable_available(name: str) -> bool:
    """检查可执行文件是否存在"""
    return find_executable(name) is not None

# ============================================================================
# Python 环境检测
# ============================================================================

@lru_cache(maxsize=1)
def get_python_version() -> str:
    """获取 Python 版本"""
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

@lru_cache(maxsize=1)
def get_venv_type() -> str:
    """检测虚拟环境类型"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        venv = os.environ.get("VIRTUAL_ENV", "")
        if "conda" in venv.lower():
            return "conda"
        return "venv"
    return "system"

# ============================================================================
# 配置加载
# ============================================================================

def load_env_file(path: str) -> None:
    """加载 .env 文件"""
    if not os.path.exists(path):
        return
    
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # 去除引号
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            os.environ.setdefault(key, value)
