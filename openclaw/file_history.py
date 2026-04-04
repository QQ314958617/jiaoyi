"""
File History - 文件历史快照系统
基于 Claude Code fileHistory.ts 设计

管理文件的版本快照，支持：
- 跟踪文件的备份版本
- 文件变更差异计算
- 快照创建和恢复
- 最多保留100个快照
"""
import difflib
import hashlib
import os
import shutil
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .errors import log_error, error_message


@dataclass
class FileHistoryBackup:
    """文件历史备份"""
    backup_file_name: Optional[str]  # None表示文件在此版本不存在
    version: int
    backup_time: datetime


@dataclass
class FileHistorySnapshot:
    """文件历史快照"""
    message_id: str  # 关联的消息ID
    tracked_file_backups: dict  # 文件路径 -> FileHistoryBackup
    timestamp: datetime


@dataclass
class DiffStats:
    """差异统计"""
    files_changed: list[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0


class FileHistory:
    """
    文件历史管理器
    
    核心功能：
    - 跟踪文件的变更快照
    - 计算文件差异统计
    - 管理备份文件
    """
    
    MAX_SNAPSHOTS = 100  # 最大快照数
    
    def __init__(
        self,
        backup_dir: Optional[str] = None,
        max_snapshots: int = 100,
    ):
        """
        Args:
            backup_dir: 备份目录
            max_snapshots: 最大快照数
        """
        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            home = os.path.expanduser("~")
            self.backup_dir = Path(home) / ".claude" / "file_backups"
        
        self.max_snapshots = max_snapshots
        self._snapshots: list[FileHistorySnapshot] = []
        self._tracked_files: set[str] = set()
        self._snapshot_sequence: int = 0
        self._lock = threading.Lock()
        
        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _compute_file_hash(self, file_path: str) -> Optional[str]:
        """计算文件内容的MD5哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    
    def track_file(self, file_path: str) -> bool:
        """
        开始跟踪一个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        abs_path = str(Path(file_path).resolve())
        
        with self._lock:
            if abs_path not in self._tracked_files:
                self._tracked_files.add(abs_path)
            return True
    
    def untrack_file(self, file_path: str) -> bool:
        """
        取消跟踪一个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        abs_path = str(Path(file_path).resolve())
        
        with self._lock:
            self._tracked_files.discard(abs_path)
            return True
    
    def create_snapshot(
        self,
        message_id: str,
        file_paths: Optional[list[str]] = None,
    ) -> Optional[FileHistorySnapshot]:
        """
        创建文件快照
        
        Args:
            message_id: 关联的消息ID
            file_paths: 要快照的文件路径列表，None表示所有跟踪的文件
            
        Returns:
            创建的快照，失败返回None
        """
        with self._lock:
            try:
                # 确定要快照的文件
                if file_paths:
                    files_to_snapshot = [str(Path(p).resolve()) for p in file_paths]
                else:
                    files_to_snapshot = list(self._tracked_files)
                
                # 创建备份
                tracked_backups = {}
                current_version = len(self._snapshots)
                
                for file_path in files_to_snapshot:
                    p = Path(file_path)
                    
                    if p.exists():
                        # 读取内容
                        content = self._read_file_content(file_path)
                        if content is None:
                            continue
                        
                        # 生成备份文件名
                        file_hash = self._compute_file_hash(file_path)[:8]
                        backup_name = f"{p.name}_{current_version}_{file_hash}.bak"
                        backup_path = self.backup_dir / backup_name
                        
                        # 复制文件
                        shutil.copy2(file_path, backup_path)
                        
                        tracked_backups[file_path] = FileHistoryBackup(
                            backup_file_name=backup_name,
                            version=current_version,
                            backup_time=datetime.now(),
                        )
                    else:
                        # 文件不存在
                        tracked_backups[file_path] = FileHistoryBackup(
                            backup_file_name=None,
                            version=current_version,
                            backup_time=datetime.now(),
                        )
                
                # 创建快照
                snapshot = FileHistorySnapshot(
                    message_id=message_id,
                    tracked_file_backups=tracked_backups,
                    timestamp=datetime.now(),
                )
                
                self._snapshots.append(snapshot)
                self._snapshot_sequence += 1
                
                # 清理旧快照
                self._cleanup_old_snapshots()
                
                return snapshot
                
            except Exception as e:
                log_error(f"Failed to create snapshot: {e}")
                return None
    
    def _cleanup_old_snapshots(self) -> None:
        """清理超过最大数量的旧快照"""
        while len(self._snapshots) > self.max_snapshots:
            old_snapshot = self._snapshots.pop(0)
            
            # 删除关联的备份文件
            for backup in old_snapshot.tracked_file_backups.values():
                if backup.backup_file_name:
                    try:
                        backup_path = self.backup_dir / backup.backup_file_name
                        if backup_path.exists():
                            backup_path.unlink()
                    except Exception:
                        pass
    
    def compute_diff(
        self,
        file_path: str,
        old_version: Optional[int] = None,
        new_version: Optional[int] = None,
    ) -> Optional[DiffStats]:
        """
        计算文件差异
        
        Args:
            file_path: 文件路径
            old_version: 旧版本索引，None表示与空文件比较
            new_version: 新版本索引，None表示与当前文件比较
            
        Returns:
            差异统计，失败返回None
        """
        abs_path = str(Path(file_path).resolve())
        
        try:
            # 获取旧内容
            if old_version is not None and 0 <= old_version < len(self._snapshots):
                old_snapshot = self._snapshots[old_version]
                old_backup = old_snapshot.tracked_file_backups.get(abs_path)
                
                if old_backup and old_backup.backup_file_name:
                    backup_path = self.backup_dir / old_backup.backup_file_name
                    if backup_path.exists():
                        with open(backup_path, 'r', encoding='utf-8') as f:
                            old_content = f.read()
                    else:
                        old_content = ""
                else:
                    old_content = ""
            else:
                old_content = ""
            
            # 获取新内容
            if new_version is not None and 0 <= new_version < len(self._snapshots):
                new_snapshot = self._snapshots[new_version]
                new_backup = new_snapshot.tracked_file_backups.get(abs_path)
                
                if new_backup and new_backup.backup_file_name:
                    backup_path = self.backup_dir / new_backup.backup_file_name
                    if backup_path.exists():
                        with open(backup_path, 'r', encoding='utf-8') as f:
                            new_content = f.read()
                    else:
                        new_content = ""
                else:
                    new_content = ""
            else:
                # 与当前文件比较
                p = Path(abs_path)
                if p.exists():
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                else:
                    new_content = ""
            
            # 计算差异
            diff = list(difflib.unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                lineterm='',
            ))
            
            insertions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
            deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
            
            return DiffStats(
                files_changed=[file_path] if diff else [],
                insertions=insertions,
                deletions=deletions,
            )
            
        except Exception as e:
            log_error(f"Failed to compute diff: {e}")
            return None
    
    def get_snapshot(self, index: int) -> Optional[FileHistorySnapshot]:
        """
        获取指定索引的快照
        
        Args:
            index: 快照索引（负数从后往前数）
            
        Returns:
            快照对象
        """
        with self._lock:
            if -len(self._snapshots) <= index < len(self._snapshots):
                return self._snapshots[index]
            return None
    
    def get_latest_snapshot(self) -> Optional[FileHistorySnapshot]:
        """获取最新的快照"""
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None
    
    def get_tracked_files(self) -> set:
        """获取当前跟踪的文件集合"""
        with self._lock:
            return set(self._tracked_files)
    
    def get_snapshot_count(self) -> int:
        """获取快照数量"""
        with self._lock:
            return len(self._snapshots)
    
    def restore_file(
        self,
        file_path: str,
        snapshot_index: int,
    ) -> bool:
        """
        从快照恢复文件
        
        Args:
            file_path: 文件路径
            snapshot_index: 快照索引
            
        Returns:
            是否恢复成功
        """
        abs_path = str(Path(file_path).resolve())
        
        try:
            snapshot = self.get_snapshot(snapshot_index)
            if not snapshot:
                return False
            
            backup = snapshot.tracked_file_backups.get(abs_path)
            if not backup or not backup.backup_file_name:
                return False
            
            backup_path = self.backup_dir / backup.backup_file_name
            if not backup_path.exists():
                return False
            
            # 恢复文件
            shutil.copy2(backup_path, abs_path)
            return True
            
        except Exception as e:
            log_error(f"Failed to restore file: {e}")
            return False
    
    def clear(self) -> None:
        """清空所有快照和备份"""
        with self._lock:
            # 删除所有备份文件
            for backup_file in self.backup_dir.glob("*.bak"):
                try:
                    backup_file.unlink()
                except Exception:
                    pass
            
            # 清空快照列表
            self._snapshots.clear()
            self._tracked_files.clear()
            self._snapshot_sequence = 0


# 全局实例
_file_history: Optional[FileHistory] = None


def get_file_history() -> FileHistory:
    """获取全局文件历史实例"""
    global _file_history
    if _file_history is None:
        _file_history = FileHistory()
    return _file_history


# 导出
__all__ = [
    "FileHistory",
    "FileHistoryBackup",
    "FileHistorySnapshot",
    "DiffStats",
    "get_file_history",
]
