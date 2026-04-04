"""
SubprocessEnv - 子进程环境
基于 Claude Code subprocess_env.ts 设计

子进程环境变量工具。
"""
import os
import subprocess
from typing import Dict, List, Optional


def run(command: List[str], env: Dict[str, str] = None, cwd: str = None) -> dict:
    """
    运行命令（使用扩展环境变量）
    
    Returns:
        {"stdout": "", "stderr": "", "exit_code": 0}
    """
    # 合并环境变量
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        env=full_env
    )
    
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
    }


def expand_env_vars(text: str) -> str:
    """展开文本中的环境变量${VAR}"""
    import re
    
    pattern = r'\$\{([^}]+)\}'
    
    def replacer(match):
        var = match.group(1)
        return os.environ.get(var, match.group(0))
    
    return re.sub(pattern, replacer, text)


def shell_expand_env_vars(text: str) -> str:
    """展开Shell风格的环境变量$VAR"""
    import re
    
    pattern = r'\$([A-Z_][A-Z0-9_]*)'
    
    def replacer(match):
        var = match.group(1)
        return os.environ.get(var, match.group(0))
    
    return re.sub(pattern, replacer, text)


def get_env_with_defaults(env: Dict[str, str], defaults: Dict[str, str]) -> Dict[str, str]:
    """
    合并环境变量与默认值
    
    Args:
        env: 环境变量字典
        defaults: 默认值
    """
    result = dict(defaults)
    result.update(env)
    return result


def child_env(parent: Dict[str, str] = None, overrides: Dict[str, str] = None) -> Dict[str, str]:
    """
    创建子进程环境
    
    Args:
        parent: 父环境（默认当前环境）
        overrides: 覆盖值
    """
    if parent is None:
        parent = os.environ
    
    result = dict(parent)
    
    if overrides:
        result.update(overrides)
    
    return result


# 导出
__all__ = [
    "run",
    "expand_env_vars",
    "shell_expand_env_vars",
    "get_env_with_defaults",
    "child_env",
]
