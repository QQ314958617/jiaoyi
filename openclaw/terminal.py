"""
Terminal - 终端
基于 Claude Code terminal.ts 设计

终端操作工具。
"""
import os
import sys
import subprocess
from typing import List, Optional


def run(command: List[str], cwd: str = None, env: dict = None) -> dict:
    """
    运行命令
    
    Returns:
        {"stdout": "", "stderr": "", "exit_code": 0}
    """
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env or os.environ.copy()
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode
    }


def get_size() -> tuple:
    """获取终端大小"""
    import shutil
    size = shutil.get_terminal_size(fallback=(80, 24))
    return size.columns, size.lines


def is_tty() -> bool:
    """是否是TTY"""
    return sys.stdout.isatty()


def clear():
    """清屏"""
    print('\033[2J\033[H', end='', flush=True)


def cursor_hide():
    """隐藏光标"""
    print('\033[?25l', end='', flush=True)


def cursor_show():
    """显示光标"""
    print('\033[?25h', end='', flush=True)


def cursor_to(x: int, y: int):
    """移动光标"""
    print(f'\033[{y};{x}H', end='', flush=True)


def get_env(key: str, default: str = None) -> str:
    """获取环境变量"""
    return os.environ.get(key, default)


def set_env(key: str, value: str):
    """设置环境变量"""
    os.environ[key] = value


def unset_env(key: str):
    """删除环境变量"""
    os.environ.pop(key, None)


class Terminal:
    """终端类"""
    
    @staticmethod
    def run(command: List[str], cwd: str = None) -> dict:
        return run(command, cwd)
    
    @staticmethod
    def size() -> tuple:
        return get_size()
    
    @staticmethod
    def clear():
        clear()
    
    @staticmethod
    def is_tty() -> bool:
        return is_tty()


# 导出
__all__ = [
    "run",
    "get_size",
    "is_tty",
    "clear",
    "cursor_hide",
    "cursor_show",
    "cursor_to",
    "get_env",
    "set_env",
    "unset_env",
    "Terminal",
]
