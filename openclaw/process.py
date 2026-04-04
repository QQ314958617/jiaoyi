"""
Process - 进程
基于 Claude Code process.ts 设计

进程工具。
"""
import os
import sys
import subprocess
from typing import List, Optional


def cwd() -> str:
    """当前工作目录"""
    return os.getcwd()


def chdir(path: str) -> None:
    """切换工作目录"""
    os.chdir(path)


def env() -> dict:
    """环境变量"""
    return dict(os.environ)


def expand_env(text: str) -> str:
    """展开环境变量${VAR}"""
    import re
    pattern = r'\$\{([^}]+)\}'
    
    def replacer(match):
        var = match.group(1)
        return os.environ.get(var, match.group(0))
    
    return re.sub(pattern, replacer, text)


def exec_(command: List[str], cwd: str = None) -> str:
    """
    执行命令
    
    Returns:
        输出字符串
    """
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr


def spawn(command: List[str], cwd: str = None) -> subprocess.Popen:
    """
    衍生进程
    """
    return subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def pid() -> int:
    """当前进程ID"""
    return os.getpid()


def parent_pid() -> int:
    """父进程ID"""
    return os.getppid()


def exit_(code: int = 0) -> None:
    """退出进程"""
    sys.exit(code)


# 导出
__all__ = [
    "cwd",
    "chdir",
    "env",
    "expand_env",
    "exec_",
    "spawn",
    "pid",
    "parent_pid",
    "exit_",
]
