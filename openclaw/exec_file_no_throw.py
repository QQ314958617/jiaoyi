"""
ExecFileNoThrow - 安全执行
基于 Claude Code exec_file_no_throw.ts 设计

安全执行文件工具。
"""
import subprocess
from typing import List, Optional, Dict


def exec_file_no_throw(
    command: List[str],
    cwd: str = None,
    timeout: int = None,
    env: dict = None
) -> Dict:
    """
    安全执行命令（不抛异常）
    
    Returns:
        {
            "success": True/False,
            "stdout": "",
            "stderr": "",
            "exit_code": 0
        }
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "exit_code": -1,
            "error": "timeout"
        }
    except FileNotFoundError as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command not found: {command[0]}",
            "exit_code": -1,
            "error": "not_found"
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "error": "unknown"
        }


def exec_shell_no_throw(
    command: str,
    cwd: str = None,
    timeout: int = None,
    env: dict = None
) -> Dict:
    """
    安全执行Shell命令（不抛异常）
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "exit_code": -1,
            "error": "timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
            "error": "unknown"
        }


# 导出
__all__ = [
    "exec_file_no_throw",
    "exec_shell_no_throw",
]
