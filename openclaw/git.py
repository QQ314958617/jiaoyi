"""
Git - Git操作
基于 Claude Code git.ts 设计

Git工具。
"""
import subprocess
from typing import List, Optional


def run(args: List[str], cwd: str = None) -> dict:
    """
    运行git命令
    
    Returns:
        {"stdout": "", "stderr": "", "returncode": 0}
    """
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return {
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode
    }


def status(cwd: str = None) -> dict:
    """获取状态"""
    return run(["status", "--porcelain"], cwd)


def diff(cwd: str = None) -> str:
    """获取diff"""
    result = run(["diff"], cwd)
    return result["stdout"]


def diff_staged(cwd: str = None) -> str:
    """获取暂存区diff"""
    result = run(["diff", "--cached"], cwd)
    return result["stdout"]


def log(cwd: str = None, n: int = 10) -> List[dict]:
    """获取提交日志"""
    result = run(["log", f"--pretty=format:%H|%s|%an", f"-{n}"], cwd)
    commits = []
    for line in result["stdout"].splitlines():
        if "|" in line:
            parts = line.split("|")
            if len(parts) == 3:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1],
                    "author": parts[2]
                })
    return commits


def branch(cwd: str = None) -> List[str]:
    """获取分支列表"""
    result = run(["branch", "-a"], cwd)
    return [b.strip().replace("* ", "") for b in result["stdout"].splitlines()]


def current_branch(cwd: str = None) -> str:
    """获取当前分支"""
    result = run(["branch", "--show-current"], cwd)
    return result["stdout"]


def add(files: List[str], cwd: str = None) -> bool:
    """添加文件到暂存区"""
    result = run(["add"] + files, cwd)
    return result["returncode"] == 0


def commit(message: str, cwd: str = None) -> bool:
    """提交"""
    result = run(["commit", "-m", message], cwd)
    return result["returncode"] == 0


def push(cwd: str = None, remote: str = "origin", branch: str = None) -> bool:
    """推送"""
    if branch:
        result = run(["push", remote, branch], cwd)
    else:
        result = run(["push"], cwd)
    return result["returncode"] == 0


def pull(cwd: str = None) -> bool:
    """拉取"""
    result = run(["pull"], cwd)
    return result["returncode"] == 0


def stash(cwd: str = None) -> bool:
    """暂存"""
    result = run(["stash"], cwd)
    return result["returncode"] == 0


def stash_pop(cwd: str = None) -> bool:
    """恢复暂存"""
    result = run(["stash", "pop"], cwd)
    return result["returncode"] == 0


def is_clean(cwd: str = None) -> bool:
    """工作区是否干净"""
    result = status(cwd)
    return result["stdout"] == ""


# 导出
__all__ = [
    "run",
    "status",
    "diff",
    "diff_staged",
    "log",
    "branch",
    "current_branch",
    "add",
    "commit",
    "push",
    "pull",
    "stash",
    "stash_pop",
    "is_clean",
]
