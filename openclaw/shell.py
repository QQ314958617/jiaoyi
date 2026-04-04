"""
Shell - Shell命令
基于 Claude Code shell.ts 设计

Shell命令工具。
"""
import subprocess
from typing import List, Optional


def run(command: str, cwd: str = None, timeout: int = None) -> dict:
    """
    运行shell命令
    
    Returns:
        {"stdout": "", "stderr": "", "exit_code": 0}
    """
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
    }


def run_async(command: str, cwd: str = None) -> subprocess.Popen:
    """
    异步运行命令
    """
    return subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def which(command: str) -> Optional[str]:
    """
    查找命令路径
    """
    result = subprocess.run(
        f"which {command}",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def exists(command: str) -> bool:
    """命令是否存在"""
    return which(command) is not None


def shell_quote(text: str) -> str:
    """Shell转义"""
    return f"'{text.replace("'", "'\\''")}'"


def shell_split(text: str) -> List[str]:
    """Shell分割"""
    import shlex
    return shlex.split(text)


class Shell:
    """Shell执行器"""
    
    def __init__(self, cwd: str = None):
        self._cwd = cwd
    
    def run(self, command: str, timeout: int = None) -> dict:
        return run(command, self._cwd, timeout)
    
    def exec(self, command: str) -> str:
        result = self.run(command)
        return result["stdout"]
    
    def test(self, command: str) -> bool:
        result = self.run(command)
        return result["exit_code"] == 0


# 导出
__all__ = [
    "run",
    "run_async",
    "which",
    "exists",
    "shell_quote",
    "shell_split",
    "Shell",
]
