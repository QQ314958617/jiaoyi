"""
Session Storage - 会话存储系统
基于 Claude Code sessionStorage.ts 设计

管理会话历史、消息持久化和恢复。
核心功能：
- 会话消息序列化/反序列化
- 会话历史文件读写
- 轻量级会话存储
- 会话恢复
"""
import json
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .errors import log_error, error_message
from .json_utils import json_parse, json_stringify


@dataclass
class MessageContent:
    """消息内容"""
    content: str | list = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> "MessageContent":
        content = data.get("content", "")
        return cls(content=content)


@dataclass
class SerializedMessage:
    """序列化消息"""
    type: str = "user"  # user, assistant, system, attachment
    id: str = ""
    message: dict = field(default_factory=dict)
    timestamp: str = ""
    is_meta: bool = False
    
    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "id": self.id,
            "message": self.message,
            "timestamp": self.timestamp,
            "isMeta": self.is_meta,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SerializedMessage":
        return cls(
            type=data.get("type", "user"),
            id=data.get("id", ""),
            message=data.get("message", {}),
            timestamp=data.get("timestamp", ""),
            is_meta=data.get("isMeta", False),
        )


@dataclass
class LogOption:
    """日志选项"""
    session_id: str = ""
    title: str = ""
    custom_title: str = ""
    tag: str = ""
    git_branch: str = ""
    summary: str = ""
    first_prompt: str = ""
    created_at: str = ""
    updated_at: str = ""
    messages: list[SerializedMessage] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "sessionId": self.session_id,
            "title": self.title,
            "customTitle": self.custom_title,
            "tag": self.tag,
            "gitBranch": self.git_branch,
            "summary": self.summary,
            "firstPrompt": self.first_prompt,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "messages": [m.to_dict() if isinstance(m, SerializedMessage) else m for m in self.messages],
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "LogOption":
        messages = [
            SerializedMessage.from_dict(m) if isinstance(m, dict) else m
            for m in data.get("messages", [])
        ]
        return cls(
            session_id=data.get("sessionId", ""),
            title=data.get("title", ""),
            custom_title=data.get("customTitle", ""),
            tag=data.get("tag", ""),
            git_branch=data.get("gitBranch", ""),
            summary=data.get("summary", ""),
            first_prompt=data.get("firstPrompt", ""),
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
            messages=messages,
        )


class SessionStorage:
    """
    会话存储管理器
    
    负责：
    - 会话历史文件的读写
    - 消息的序列化/反序列化
    - 会话恢复
    - 轻量级会话存储（Lite模式）
    """
    
    def __init__(
        self,
        storage_dir: Optional[str] = None,
        max_file_size_mb: int = 10,
    ):
        """
        Args:
            storage_dir: 存储目录，默认~/.claude/sessions
            max_file_size_mb: 单个会话文件最大大小（MB）
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            home = os.path.expanduser("~")
            self.storage_dir = Path(home) / ".claude" / "sessions"
        
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self._lock = threading.Lock()
        
        # 确保目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_path(self, session_id: str) -> Path:
        """获取会话文件路径"""
        return self.storage_dir / f"{session_id}.json"
    
    def save_message(
        self,
        session_id: str,
        message: SerializedMessage,
    ) -> bool:
        """
        保存单条消息到会话
        
        Args:
            session_id: 会话ID
            message: 消息对象
            
        Returns:
            是否保存成功
        """
        with self._lock:
            try:
                session_path = self._get_session_path(session_id)
                
                # 读取现有数据
                if session_path.exists():
                    with open(session_path, 'r', encoding='utf-8') as f:
                        data = json_parse(f.read())
                else:
                    data = {"messages": []}
                
                # 添加消息
                data.setdefault("messages", []).append(message.to_dict())
                
                # 写回文件
                with open(session_path, 'w', encoding='utf-8') as f:
                    f.write(json_stringify(data))
                
                return True
                
            except Exception as e:
                log_error(f"Failed to save message: {e}")
                return False
    
    def load_session(
        self,
        session_id: str,
        include_messages: bool = True,
    ) -> Optional[LogOption]:
        """
        加载会话
        
        Args:
            session_id: 会话ID
            include_messages: 是否加载消息内容
            
        Returns:
            会话数据，失败返回None
        """
        try:
            session_path = self._get_session_path(session_id)
            if not session_path.exists():
                return None
            
            with open(session_path, 'r', encoding='utf-8') as f:
                data = json_parse(f.read())
            
            log = LogOption.from_dict(data)
            
            # 轻量模式：只加载元数据，不加载消息
            if not include_messages:
                log.messages = []
            
            return log
            
        except Exception as e:
            log_error(f"Failed to load session {session_id}: {e}")
            return None
    
    def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LogOption]:
        """
        列出所有会话（轻量模式，只加载元数据）
        
        Args:
            limit: 返回数量限制
            offset: 跳过数量
            
        Returns:
            会话列表（按更新时间倒序）
        """
        sessions = []
        
        try:
            for file_path in self.storage_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json_parse(f.read())
                    
                    # 轻量模式：不加载messages字段以节省内存
                    if "messages" in data:
                        del data["messages"]
                    
                    sessions.append(LogOption.from_dict(data))
                    
                except Exception:
                    continue
            
            # 按更新时间倒序
            sessions.sort(
                key=lambda s: s.updated_at or s.created_at or "",
                reverse=True
            )
            
            return sessions[offset:offset + limit]
            
        except Exception as e:
            log_error(f"Failed to list sessions: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        with self._lock:
            try:
                session_path = self._get_session_path(session_id)
                if session_path.exists():
                    session_path.unlink()
                return True
            except Exception as e:
                log_error(f"Failed to delete session {session_id}: {e}")
                return False
    
    def save_session(
        self,
        session_id: str,
        log: LogOption,
    ) -> bool:
        """
        保存完整会话
        
        Args:
            session_id: 会话ID
            log: 会话数据
            
        Returns:
            是否保存成功
        """
        with self._lock:
            try:
                log.session_id = session_id
                log.updated_at = datetime.now().isoformat()
                
                session_path = self._get_session_path(session_id)
                
                with open(session_path, 'w', encoding='utf-8') as f:
                    f.write(json_stringify(log.to_dict()))
                
                return True
                
            except Exception as e:
                log_error(f"Failed to save session: {e}")
                return False
    
    def get_storage_size(self) -> dict:
        """
        获取存储大小统计
        
        Returns:
            {"file_count": int, "total_bytes": int, "total_mb": float}
        """
        total_bytes = 0
        file_count = 0
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                total_bytes += file_path.stat().st_size
                file_count += 1
            except Exception:
                continue
        
        return {
            "file_count": file_count,
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
        }


# 全局会话存储实例
_session_storage: Optional[SessionStorage] = None


def get_session_storage() -> SessionStorage:
    """获取全局会话存储实例"""
    global _session_storage
    if _session_storage is None:
        _session_storage = SessionStorage()
    return _session_storage


# 导出
__all__ = [
    "SessionStorage",
    "SerializedMessage",
    "LogOption",
    "get_session_storage",
]
