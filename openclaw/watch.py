"""
Watch - 文件监控
基于 Claude Code watch.ts 设计

文件变化监控工具。
"""
import os
import threading
import time
from typing import Callable, Optional, Set


class FileWatcher:
    """
    文件监控器
    
    监控文件变化并触发回调。
    """
    
    def __init__(
        self,
        callback: Callable[[str, str], None],  # (path, event_type)
        interval_seconds: float = 1.0,
    ):
        """
        Args:
            callback: 变化回调函数 (path, event_type)
            interval_seconds: 检查间隔
        """
        self._callback = callback
        self._interval = interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._files: Set[str] = set()
        self._mtimes: dict = {}
        self._lock = threading.Lock()
    
    def add_file(self, path: str) -> None:
        """添加监控文件"""
        with self._lock:
            self._files.add(path)
            try:
                self._mtimes[path] = os.path.getmtime(path)
            except Exception:
                pass
    
    def remove_file(self, path: str) -> None:
        """移除监控文件"""
        with self._lock:
            self._files.discard(path)
            self._mtimes.pop(path, None)
    
    def start(self) -> None:
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
    
    def _watch_loop(self) -> None:
        """监控循环"""
        while self._running:
            time.sleep(self._interval)
            self._check_changes()
    
    def _check_changes(self) -> None:
        """检查变化"""
        with self._lock:
            files = list(self._files)
            mtimes = dict(self._mtimes)
        
        for path in files:
            try:
                current_mtime = os.path.getmtime(path)
                old_mtime = mtimes.get(path)
                
                if old_mtime is None:
                    # 新文件
                    self._callback(path, 'add')
                elif current_mtime > old_mtime:
                    # 修改
                    self._callback(path, 'modify')
                
                with self._lock:
                    self._mtimes[path] = current_mtime
                    
            except FileNotFoundError:
                # 文件删除
                with self._lock:
                    self._mtimes.pop(path, None)
                self._callback(path, 'delete')
            except Exception:
                pass


class DirectoryWatcher:
    """
    目录监控器
    
    监控目录下文件的变化。
    """
    
    def __init__(
        self,
        directory: str,
        callback: Callable[[str, str], None],
        interval_seconds: float = 1.0,
        recursive: bool = True,
    ):
        """
        Args:
            directory: 目录路径
            callback: 变化回调
            interval_seconds: 检查间隔
            recursive: 是否递归子目录
        """
        self._directory = directory
        self._callback = callback
        self._interval = interval_seconds
        self._recursive = recursive
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._file_watcher: Optional[FileWatcher] = None
    
    def start(self) -> None:
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        
        # 创建文件监控器
        self._file_watcher = FileWatcher(self._callback, self._interval)
        
        # 添加目录下的所有文件
        self._scan_directory()
        
        # 启动监控
        self._file_watcher.start()
        
        # 启动定期扫描以检测新文件
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """停止监控"""
        self._running = False
        if self._file_watcher:
            self._file_watcher.stop()
        if self._thread:
            self._thread.join(timeout=5)
    
    def _scan_directory(self) -> None:
        """扫描目录"""
        if not os.path.exists(self._directory):
            return
        
        for entry in self._walk_directory(self._directory):
            if self._file_watcher:
                self._file_watcher.add_file(entry)
    
    def _walk_directory(self, path: str):
        """遍历目录"""
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    yield entry.path
                    if self._recursive and entry.is_dir():
                        yield from self._walk_directory(entry.path)
        except PermissionError:
            pass
    
    def _scan_loop(self) -> None:
        """定期扫描循环"""
        while self._running:
            time.sleep(self._interval)
            self._scan_directory()


# 导出
__all__ = [
    "FileWatcher",
    "DirectoryWatcher",
]
