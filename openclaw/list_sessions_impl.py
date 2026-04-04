"""
ListSessionsImpl - 会话列表
基于 Claude Code list_sessions_impl.ts 设计

会话列表工具。
"""
import os
import json
from typing import List, Optional, Dict


def list_sessions(sessions_dir: str = None) -> List[Dict]:
    """
    列出所有会话
    
    Args:
        sessions_dir: 会话目录
        
    Returns:
        [{"id": "...", "path": "...", "modified": ...}]
    """
    if sessions_dir is None:
        sessions_dir = os.path.expanduser("~/.claude/sessions")
    
    if not os.path.exists(sessions_dir):
        return []
    
    sessions = []
    
    for name in os.listdir(sessions_dir):
        path = os.path.join(sessions_dir, name)
        if os.path.isdir(path):
            sessions.append({
                "id": name,
                "path": path,
                "modified": os.path.getmtime(path),
            })
    
    return sorted(sessions, key=lambda x: x["modified"], reverse=True)


def read_session_meta(session_path: str) -> Optional[Dict]:
    """
    读取会话元数据
    
    Args:
        session_path: 会话路径
    """
    meta_file = os.path.join(session_path, ".meta.json")
    
    if not os.path.exists(meta_file):
        return None
    
    try:
        with open(meta_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def delete_session(session_path: str) -> bool:
    """
    删除会话
    
    Args:
        session_path: 会话路径
    """
    import shutil
    
    if os.path.exists(session_path):
        shutil.rmtree(session_path)
        return True
    return False


def get_active_session(sessions_dir: str = None) -> Optional[str]:
    """
    获取当前活跃会话
    
    Args:
        sessions_dir: 会话目录
    """
    if sessions_dir is None:
        sessions_dir = os.path.expanduser("~/.claude/sessions")
    
    active_link = os.path.join(sessions_dir, "current")
    
    if os.path.islink(active_link):
        return os.readlink(active_link)
    
    return None


# 导出
__all__ = [
    "list_sessions",
    "read_session_meta",
    "delete_session",
    "get_active_session",
]
