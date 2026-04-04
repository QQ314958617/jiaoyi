"""
Exec File Utilities - 进程执行工具
基于 Claude Code execFileNoThrow.ts 设计

提供安全的进程执行封装。
"""
import subprocess
import threading
from dataclasses import dataclass
from typing import Any, Optional

from .errors import log_error


@dataclass
class ExecResult:
    """执行结果"""
    stdout: str = ""
    stderr: str = ""
    code: int = 0
    error: Optional[str] = None


# 默认超时（10分钟）
DEFAULT_TIMEOUT_MS = 10 * 60 * 1000


def exec_file_no_throw(
    file: str,
    args: list[str],
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    input_str: Optional[str] = None,
) -> ExecResult:
    """
    执行命令，始终返回结果（不抛异常）
    
    Args:
        file: 可执行文件路径
        args: 命令参数
        timeout_ms: 超时毫秒
        cwd: 工作目录
        env: 环境变量
        input_str: 标准输入
        
    Returns:
        执行结果
    """
    try:
        # 构建参数
        exec_kwargs: dict[str, Any] = {
            'capture_output': True,
            'text': True,
            'timeout': timeout_ms / 1000,
        }
        
        if cwd:
            exec_kwargs['cwd'] = cwd
        
        if env:
            exec_kwargs['env'] = {**subprocess.os.environ, **env}
        
        if input_str:
            exec_kwargs['input'] = input_str
        
        result = subprocess.run(
            [file] + args,
            **exec_kwargs,
        )
        
        return ExecResult(
            stdout=result.stdout or "",
            stderr=result.stderr or "",
            code=result.returncode,
        )
        
    except subprocess.TimeoutExpired as e:
        return ExecResult(
            stdout=e.stdout.decode() if e.stdout else "",
            stderr=e.stderr.decode() if e.stderr else "",
            code=-1,
            error="TimeoutExpired",
        )
        
    except FileNotFoundError:
        return ExecResult(
            code=-1,
            error=f"Command not found: {file}",
        )
        
    except Exception as e:
        log_error(f"exec_file_no_throw error: {e}")
        return ExecResult(
            code=-1,
            error=str(e),
        )


async def exec_file_no_throw_async(
    file: str,
    args: list[str],
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
) -> ExecResult:
    """
    异步执行命令
    
    Args:
        file: 可执行文件路径
        args: 命令参数
        timeout_ms: 超时毫秒
        cwd: 工作目录
        env: 环境变量
        
    Returns:
        执行结果
    """
    import asyncio
    
    try:
        # 构建参数
        exec_kwargs: dict[str, Any] = {
            'capture_output': True,
            'text': True,
        }
        
        if cwd:
            exec_kwargs['cwd'] = cwd
        
        if env:
            exec_kwargs['env'] = {**subprocess.os.environ.copy(), **env}
        
        proc = await asyncio.create_subprocess_exec(
            file,
            *args,
            **exec_kwargs,
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_ms / 1000,
            )
            
            return ExecResult(
                stdout=stdout or "",
                stderr=stderr or "",
                code=proc.returncode or 0,
            )
            
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return ExecResult(
                code=-1,
                error="TimeoutExpired",
            )
            
    except Exception as e:
        log_error(f"exec_file_no_throw_async error: {e}")
        return ExecResult(
            code=-1,
            error=str(e),
        )


# 导出
__all__ = [
    "ExecResult",
    "exec_file_no_throw",
    "exec_file_no_throw_async",
    "DEFAULT_TIMEOUT_MS",
]
