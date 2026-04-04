"""
Progress - 进度
基于 Claude Code progress.ts 设计

进度条工具。
"""
from typing import Optional


class Progress:
    """进度条"""
    
    def __init__(self, total: int = 100, width: int = 40):
        self._total = total
        self._current = 0
        self._width = width
    
    def update(self, current: int) -> None:
        self._current = min(current, self._total)
    
    def increment(self, delta: int = 1) -> None:
        self._current = min(self._current + delta, self._total)
    
    @property
    def percent(self) -> float:
        if self._total == 0:
            return 0
        return (self._current / self._total) * 100
    
    @property
    def filled(self) -> int:
        return int(self._width * self._current / self._total) if self._total > 0 else 0
    
    @property
    def empty(self) -> int:
        return self._width - self.filled
    
    def __str__(self) -> str:
        bar = '█' * self.filled + '░' * self.empty
        return f"[{bar}] {self.percent:.1f}%"


def progress_bar(current: int, total: int, width: int = 40) -> str:
    """简单进度条字符串"""
    filled = int(width * current / total) if total > 0 else 0
    percent = (current / total * 100) if total > 0 else 0
    return f"[{'█' * filled}{'░' * (width - filled)}] {percent:.1f}%"


# 导出
__all__ = [
    "Progress",
    "progress_bar",
]
