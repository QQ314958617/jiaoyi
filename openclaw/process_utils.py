"""
OpenClaw Process Utilities
====================
Inspired by Claude Code's src/utils/process.ts.

进程工具，支持：
1. 进程信息
2. 信号处理
3. 退出管理
4. 环境变量
"""

from __future__ import annotations

import os, sys, signal, atexit, resource
from typing import Callable, Optional

# ============================================================================
# 进程信息
# ============================================================================

def get_pid() -> int:
    """获取当前进程 ID"""
    return os.getpid()

def get_parent_pid() -> int:
    """获取父进程 ID"""
    return os.getppid()

def get_uid() -> int:
    """获取当前用户 ID"""
    return os.getuid()

def get_username() -> str:
    """获取当前用户名"""
    return os.getlogin()

def is_running_as_root() -> bool:
    """检查是否以 root 运行"""
    return os.getuid() == 0

# ============================================================================
# 环境信息
# ============================================================================

def get_platform() -> str:
    """获取平台"""
    return sys.platform

def get_python_executable() -> str:
    """获取 Python 解释器路径"""
    return sys.executable

def get_python_version() -> str:
    """获取 Python 版本"""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

def get_os_version() -> str:
    """获取操作系统版本"""
    import platform
    return platform.platform()

# ============================================================================
# 资源限制
# ============================================================================

def set_max_open_files(limit: int) -> None:
    """设置最大打开文件数"""
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (min(limit, hard), hard))
    except (ValueError, OSError):
        pass

def get_max_open_files() -> tuple:
    """获取最大打开文件数限制"""
    try:
        return resource.getrlimit(resource.RLIMIT_NOFILE)
    except (ValueError, OSError):
        return (-1, -1)

def get_memory_usage() -> dict:
    """获取内存使用情况"""
    try:
        import psutil
        process = psutil.Process()
        mem = process.memory_info()
        return {
            "rss": mem.rss,  # 物理内存
            "vms": mem.vms,  # 虚拟内存
            "percent": process.memory_percent(),
        }
    except ImportError:
        # 使用 resource 模块的简单估算
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return {
            "maxrss": usage.maxrss,  # Linux: KB, macOS: bytes
        }

# ============================================================================
# 信号处理
# ============================================================================

_signal_handlers: dict = {}

def signal_handler(signum: int, callback: Callable) -> None:
    """
    注册信号处理器
    
    Args:
        signum: 信号编号
        callback: 回调函数
    """
    def wrapper(signum, frame):
        callback()
    
    signal.signal(signum, wrapper)

def ignore_signal(signum: int) -> None:
    """忽略信号"""
    signal.signal(signum, signal.SIG_IGN)

def default_signal(signum: int) -> None:
    """恢复信号默认行为"""
    signal.signal(signum, signal.SIG_DFL)

# 常用信号常量
SIGTERM = signal.SIGTERM  # 终止信号
SIGINT = signal.SIGINT   # 中断信号 (Ctrl+C)
SIGKILL = signal.SIGKILL # 杀死信号
SIGUSR1 = signal.SIGUSR1 # 用户自定义信号1
SIGUSR2 = signal.SIGUSR2 # 用户自定义信号2
SIGHUP = signal.SIGHUP    # 挂起信号

# ============================================================================
# 退出管理
# ============================================================================

_exit_handlers: list[Callable] = []
_registered_atexit = False

def _run_exit_handlers():
    """运行所有退出处理器"""
    for handler in _exit_handlers:
        try:
            handler()
        except Exception:
            pass

def register_exit_handler(callback: Callable) -> None:
    """
    注册退出处理器
    
    Args:
        callback: 退出时调用的函数
    """
    global _registered_atexit
    
    if callback not in _exit_handlers:
        _exit_handlers.append(callback)
    
    if not _registered_atexit:
        atexit.register(_run_exit_handlers)
        _registered_atexit = True

def unregister_exit_handler(callback: Callable) -> bool:
    """移除退出处理器"""
    if callback in _exit_handlers:
        _exit_handlers.remove(callback)
        return True
    return False

def exit_with_code(code: int = 0) -> None:
    """带代码退出"""
    sys.exit(code)

def abort() -> None:
    """异常终止"""
    os.abort()

# ============================================================================
# 子进程管理
# ============================================================================

def kill_process(pid: int, signum: int = SIGTERM) -> bool:
    """
    向进程发送信号
    
    Returns:
        True if successful
    """
    try:
        os.kill(pid, signum)
        return True
    except OSError:
        return False

def is_process_alive(pid: int) -> bool:
    """检查进程是否存活"""
    try:
        os.kill(pid, 0)  # 发送空信号
        return True
    except OSError:
        return False

# ============================================================================
# 环境变量
# ============================================================================

def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """获取环境变量"""
    return os.environ.get(key, default)

def set_env(key: str, value: str) -> None:
    """设置环境变量"""
    os.environ[key] = value

def unset_env(key: str) -> None:
    """删除环境变量"""
    os.environ.pop(key, None)

def get_all_env() -> dict:
    """获取所有环境变量"""
    return dict(os.environ)

# ============================================================================
# 工作目录
# ============================================================================

def get_cwd() -> str:
    """获取当前工作目录"""
    return os.getcwd()

def set_cwd(path: str) -> None:
    """设置当前工作目录"""
    os.chdir(path)

# ============================================================================
# 命令行参数
# ============================================================================

def get_args() -> list[str]:
    """获取命令行参数"""
    return sys.argv

def get_argv0() -> str:
    """获取程序名称"""
    return sys.argv[0] if sys.argv else ""

def get_argv1() -> Optional[str]:
    """获取第一个参数"""
    return sys.argv[1] if len(sys.argv) > 1 else None
