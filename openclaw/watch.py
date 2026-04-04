"""
Watch - 监控
基于 Claude Code watch.ts 设计

文件监控工具。
"""
import os
import time
from typing import Callable, List


class Watcher:
    """
    文件监控器
    """
    
    def __init__(self, path: str, handler: Callable):
        """
        Args:
            path: 监控路径
            handler: 回调函数(files_changed: List[str])
        """
        self._path = path
        self._handler = handler
        self._running = False
        self._last_mtimes = {}
    
    def start(self, interval: float = 1.0):
        """开始监控"""
        self._running = True
        self._scan()
        
        while self._running:
            time.sleep(interval)
            self._check()
    
    def stop(self):
        """停止监控"""
        self._running = False
    
    def _scan(self):
        """扫描初始状态"""
        self._last_mtimes = {}
        for root, dirs, files in os.walk(self._path):
            for name in files:
                path = os.path.join(root, name)
                try:
                    self._last_mtimes[path] = os.path.getmtime(path)
                except OSError:
                    pass
    
    def _check(self):
        """检查变更"""
        changed = []
        current_mtimes = {}
        
        for root, dirs, files in os.walk(self._path):
            for name in files:
                path = os.path.join(root, name)
                try:
                    mtime = os.path.getmtime(path)
                    current_mtimes[path] = mtime
                    
                    if path not in self._last_mtimes:
                        changed.append(path)
                    elif mtime > self._last_mtimes[path]:
                        changed.append(path)
                except OSError:
                    pass
        
        # 检测删除
        for path in self._last_mtimes:
            if path not in current_mtimes:
                changed.append(path)
        
        if changed:
            self._handler(changed)
        
        self._last_mtimes = current_mtimes


def watch(path: str, handler: Callable, interval: float = 1.0):
    """
    监控目录
    
    Args:
        path: 目录路径
        handler: 回调函数
        interval: 检查间隔
    """
    watcher = Watcher(path, handler)
    watcher.start(interval)


# 导出
__all__ = [
    "Watcher",
    "watch",
]
