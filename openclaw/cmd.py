"""
Cmd - 命令
基于 Claude Code cmd.ts 设计

命令工具。
"""
import subprocess
from typing import List


def cmd(*args) -> str:
    """
    执行命令（列表形式）
    """
    result = subprocess.run(
        list(args),
        capture_output=True,
        text=True
    )
    return result.stdout


def cmd_async(*args) -> subprocess.Popen:
    """
    异步执行命令
    """
    return subprocess.Popen(
        list(args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def which(prog: str) -> str:
    """查找程序路径"""
    result = subprocess.run(
        ["which", prog],
        capture_output=True,
        text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def success(*args) -> bool:
    """命令是否成功"""
    result = subprocess.run(list(args), capture_output=True)
    return result.returncode == 0


def output(*args) -> str:
    """获取命令输出"""
    result = subprocess.run(
        list(args),
        capture_output=True,
        text=True
    )
    return result.stdout


# 导出
__all__ = [
    "cmd",
    "cmd_async",
    "which",
    "success",
    "output",
]
