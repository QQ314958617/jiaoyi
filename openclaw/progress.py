"""
Progress - 进度
基于 Claude Code progress.ts 设计

进度工具。
"""
from typing import Optional


class Progress:
    """
    进度条
    """
    
    def __init__(self, total: int = 100, width: int = 40, show_percent: bool = True):
        """
        Args:
            total: 总数
            width: 进度条宽度
            show_percent: 显示百分比
        """
        self._total = total
        self._current = 0
        self._width = width
        self._show_percent = show_percent
    
    def update(self, current: int) -> None:
        """
        更新进度
        
        Args:
            current: 当前进度
        """
        self._current = min(current, self._total)
    
    def increment(self, delta: int = 1) -> None:
        """增加进度"""
        self._current = min(self._current + delta, self._total)
    
    @property
    def percent(self) -> float:
        """完成百分比"""
        if self._total == 0:
            return 0
        return (self._current / self._total) * 100
    
    @property
    def filled(self) -> int:
        """已填充宽度"""
        return int(self._width * self._current / self._total) if self._total > 0 else 0
    
    @property
    def empty(self) -> int:
        """未填充宽度"""
        return self._width - self.filled
    
    def __str__(self) -> str:
        """格式化输出"""
        bar = '█' * self.filled + '░' * self.empty
        if self._show_percent:
            return f"[{bar}] {self.percent:.1f}%"
        return f"[{bar}]"
    
    def __repr__(self) -> str:
        return f"Progress({self._current}/{self._total})"


class MultiProgress:
    """
    多进度条
    """
    
    def __init__(self):
        self._bars = []
    
    def add(self, total: int = 100, label: str = "") -> Progress:
        """
        添加进度条
        
        Args:
            total: 总数
            label: 标签
            
        Returns:
            Progress实例
        """
        bar = Progress(total)
        bar._label = label
        self._bars.append(bar)
        return bar
    
    def remove(self, bar: Progress) -> None:
        """移除进度条"""
        if bar in self._bars:
            self._bars.remove(bar)
    
    def render(self) -> str:
        """渲染所有进度条"""
        return '\n'.join(str(bar) for bar in self._bars)
    
    def clear(self) -> None:
        """清空"""
        self._bars.clear()


def progress_bar(current: int, total: int, width: int = 40) -> str:
    """
    简单进度条字符串
    
    Args:
        current: 当前进度
        total: 总数
        width: 宽度
        
    Returns:
        进度条字符串
    """
    filled = int(width * current / total) if total > 0 else 0
    empty = width - filled
    percent = (current / total * 100) if total > 0 else 0
    return f"[{'█' * filled}{'░' * empty}] {percent:.1f}%"


# 导出
__all__ = [
    "Progress",
    "MultiProgress",
    "progress_bar",
]
