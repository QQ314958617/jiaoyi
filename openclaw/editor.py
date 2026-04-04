"""
Editor - 编辑器
基于 Claude Code editor.ts 设计

编辑器操作工具。
"""
import os
import subprocess
from typing import Optional


def open_in_editor(file_path: str, line: int = None, col: int = None, 
                   editor: str = None):
    """
    在编辑器中打开文件
    
    Args:
        file_path: 文件路径
        line: 行号
        col: 列号
        editor: 编辑器 (vim, nano, code, etc.)
    """
    if editor is None:
        editor = os.environ.get('EDITOR', 'vim')
    
    cmd = [editor, file_path]
    
    if line is not None:
        cmd.append(f"+{line}")
        if col is not None:
            cmd[-1] = f"+{line},{col}"
    
    subprocess.run(cmd)


def open_in_vscode(file_path: str, line: int = None):
    """在VSCode中打开"""
    cmd = ["code", "--goto", f"{file_path}:{line or 1}"]
    subprocess.run(cmd)


def open_in_vim(file_path: str, line: int = None):
    """在Vim中打开"""
    cmd = ["vim"]
    if line is not None:
        cmd.append(f"+{line}")
    cmd.append(file_path)
    subprocess.run(cmd)


def read_with_editor(file_path: str, editor: str = None) -> Optional[str]:
    """
    用编辑器读取文件内容
    """
    if editor is None:
        editor = os.environ.get('EDITOR', 'vim')
    
    # 使用编辑器打开并读取
    # 注意：这在交互式环境下才能工作
    try:
        result = subprocess.run(
            [editor, file_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            with open(file_path, 'r') as f:
                return f.read()
        return None
    except Exception:
        return None


def edit_interactive(file_path: str, editor: str = None) -> bool:
    """
    交互式编辑文件
    """
    if editor is None:
        editor = os.environ.get('EDITOR', 'vim')
    
    result = subprocess.run([editor, file_path])
    return result.returncode == 0


# 导出
__all__ = [
    "open_in_editor",
    "open_in_vscode",
    "open_in_vim",
    "read_with_editor",
    "edit_interactive",
]
