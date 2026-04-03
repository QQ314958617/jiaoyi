"""
OpenClaw File Watcher
=====================
Inspired by Claude Code's src/utils/hooks/fileChangedWatcher.ts.

核心功能：
1. 文件变化监控（create/modify/delete）
2. 防抖处理（debounce）
3. 变化时执行回调
4. 通配符支持

用途：
- 配置文件热更新（.env 改了自动重载）
- 交易历史文件监控
- 策略文件改动检测
"""

from __future__ import annotations

import os
import time
import threading
import fnmatch
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict
from enum import Enum
from pathlib import Path


# ============================================================================
# 事件类型
# ============================================================================

class FileEvent(str, Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


# ============================================================================
# 文件事件
# ============================================================================

@dataclass
class FileChange:
    """文件变化事件"""
    path: str
    event: FileEvent
    timestamp: float = field(default_factory=time.time)
    old_path: Optional[str] = None  # for MOVED


# ============================================================================
# 文件过滤器
# ============================================================================

@dataclass
class FileFilter:
    """文件过滤器"""
    patterns: List[str] = field(default_factory=list)  # glob patterns
    ignore_patterns: List[str] = field(default_factory=list)
    check_content: bool = False  # 是否检查内容变化（开销大）

    def matches(self, path: str) -> bool:
        """检查路径是否匹配"""
        # 检查忽略模式
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                return False

        # 检查匹配模式
        if not self.patterns:
            return True

        for pattern in self.patterns:
            if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
                return True

        return False


# ============================================================================
# Polling 文件监控器（无外部依赖）
# ============================================================================

class PollingWatcher:
    """
    基于轮询的文件监控器。

    使用 stat mtime 轮询检测变化。
    适合不频繁变化的配置文件监控。

    对应 Claude Code chokidar 的简单替代。

    用法：
        watcher = PollingWatcher()
        watcher.watch("/path/to/.env", callback)
        watcher.watch("*.json", callback)
        # ... later ...
        watcher.stop()
    """

    def __init__(
        self,
        poll_interval: float = 1.0,  # 轮询间隔（秒）
        debounce: float = 0.5,  # 防抖延迟
    ):
        self.poll_interval = poll_interval
        self.debounce = debounce
        self._watches: Dict[str, Callable] = {}  # path_pattern -> callback
        self._filters: Dict[str, FileFilter] = {}  # path_pattern -> filter
        self._file_mtimes: Dict[str, float] = {}  # path -> last mtime
        self._file_md5: Dict[str, str] = {}  # path -> last md5 (if check_content)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._pending_changes: Dict[str, float] = {}  # path -> first_detected_time

    def watch(
        self,
        path_or_pattern: str,
        callback: Callable[[FileChange], None],
        filter: Optional[FileFilter] = None,
    ) -> None:
        """
        添加监控。

        Args:
            path_or_pattern: 文件路径或通配符模式（如 "*.json", "/path/to/.env"）
            callback: 变化时的回调函数
            filter: 可选的过滤器
        """
        with self._lock:
            self._watches[path_or_pattern] = callback
            if filter:
                self._filters[path_or_pattern] = filter

            # 如果是具体路径，记录初始 mtime
            if os.path.isfile(path_or_pattern):
                try:
                    self._file_mtimes[path_or_pattern] = os.path.getmtime(path_or_pattern)
                except OSError:
                    pass

    def unwatch(self, path_or_pattern: str) -> bool:
        """取消监控"""
        with self._lock:
            if path_or_pattern in self._watches:
                del self._watches[path_or_pattern]
                self._filters.pop(path_or_pattern, None)
                return True
            return False

    def start(self) -> None:
        """启动监控线程"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def _poll_loop(self) -> None:
        """轮询循环"""
        import hashlib

        while self._running:
            now = time.time()
            to_fire: List[tuple[str, FileChange]] = []

            with self._lock:
                # 检查每个监控的路径
                for pattern, callback in list(self._watches.items()):
                    # 解析模式
                    if "*" in pattern or "?" in pattern:
                        # 通配符模式 - 找匹配的文件
                        dir_path = os.path.dirname(pattern) or "."
                        base_pattern = os.path.basename(pattern)
                        if os.path.isdir(dir_path):
                            try:
                                for entry in os.listdir(dir_path):
                                    full_path = os.path.join(dir_path, entry)
                                    if fnmatch.fnmatch(entry, base_pattern):
                                        self._check_file(full_path, now)
                            except OSError:
                                pass
                    else:
                        # 具体路径
                        self._check_file(pattern, now)

                # 处理待触发事件（防抖）
                for path, first_time in list(self._pending_changes.items()):
                    if now - first_time >= self.debounce:
                        # 延迟到了，触发
                        to_fire.append((path, FileChange(
                            path=path,
                            event=FileEvent.MODIFIED,
                            timestamp=first_time
                        )))
                        del self._pending_changes[path]

            # 触发回调（锁外）
            for path, change in to_fire:
                try:
                    for pattern, callback in list(self._watches.items()):
                        if fnmatch.fnmatch(path, pattern) or path == pattern:
                            # 检查过滤器
                            filter = self._filters.get(pattern)
                            if filter and not filter.matches(path):
                                continue
                            callback(change)
                            break
                except Exception as e:
                    print(f"File watcher callback error: {e}")

            time.sleep(self.poll_interval)

    def _check_file(self, path: str, now: float) -> None:
        """检查单个文件"""
        # 检查过滤器
        matched = False
        for pattern, filter in self._filters.items():
            if fnmatch.fnmatch(path, pattern) or path == pattern:
                if filter and not filter.matches(path):
                    continue
                matched = True
                break
        if not matched:
            # 没有匹配的过滤器，用默认规则
            pass

        if not os.path.exists(path):
            # 文件被删除
            if path in self._file_mtimes:
                del self._file_mtimes[path]
                change = FileChange(path=path, event=FileEvent.DELETED, timestamp=now)
                self._pending_changes[path] = now
        else:
            try:
                mtime = os.path.getmtime(path)
                old_mtime = self._file_mtimes.get(path)

                if old_mtime is None:
                    # 新文件
                    self._file_mtimes[path] = mtime
                    change = FileChange(path=path, event=FileEvent.CREATED, timestamp=now)
                    self._pending_changes[path] = now
                elif mtime > old_mtime:
                    # 被修改
                    self._file_mtimes[path] = mtime
                    change = FileChange(path=path, event=FileEvent.MODIFIED, timestamp=now)
                    self._pending_changes[path] = now

            except OSError:
                pass


# ============================================================================
# 便捷函数
# ============================================================================

_global_watcher: Optional[PollingWatcher] = None
_watcher_lock = threading.Lock()


def get_global_watcher() -> PollingWatcher:
    """获取全局文件监控器"""
    global _global_watcher
    if _global_watcher is None:
        with _watcher_lock:
            if _global_watcher is None:
                _global_watcher = PollingWatcher()
                _global_watcher.start()
    return _global_watcher


def watch_file(
    path_or_pattern: str,
    callback: Callable[[FileChange], None],
    filter: Optional[FileFilter] = None,
) -> None:
    """全局监控文件变化"""
    get_global_watcher().watch(path_or_pattern, callback, filter)


def unwatch_file(path_or_pattern: str) -> bool:
    """取消全局监控"""
    return get_global_watcher().unwatch(path_or_pattern)


def stop_global_watcher() -> None:
    """停止全局监控"""
    global _global_watcher
    if _global_watcher:
        _global_watcher.stop()
        _global_watcher = None


# ============================================================================
# 交易系统专用监控
# ============================================================================

def setup_config_watcher(
    config_paths: List[str],
    on_change: Callable[[str], None],
) -> PollingWatcher:
    """
    监控配置文件变化。

    Args:
        config_paths: 配置文件路径列表
        on_change: 变化时的回调（参数是变化的路径）

    用途：
        # 监控 .env 变化时重载配置
        setup_config_watcher([".env", "config.json"], lambda p: reload_config())
    """
    watcher = PollingWatcher(poll_interval=2.0, debounce=1.0)

    def callback(change: FileChange):
        on_change(change.path)

    for path in config_paths:
        watcher.watch(path, callback)

    watcher.start()
    return watcher
