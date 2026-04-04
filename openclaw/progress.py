"""
Progress - 进度条
基于 Claude Code progress.ts 设计

进度条工具。
"""
import sys
import time
from typing import Optional


class ProgressBar:
    """
    进度条
    """
    
    def __init__(
        self,
        total: int,
        desc: str = '',
        width: int = 40,
        show_percent: bool = True,
        show_count: bool = True,
    ):
        """
        Args:
            total: 总数
            desc: 描述
            width: 进度条宽度
            show_percent: 显示百分比
            show_count: 显示计数
        """
        self.total = total
        self.desc = desc
        self.width = width
        self.show_percent = show_percent
        self.show_count = show_count
        
        self.current = 0
        self._start_time = time.time()
    
    def update(self, n: int = 1) -> None:
        """更新进度"""
        self.current += n
        self.render()
    
    def set(self, value: int) -> None:
        """设置进度"""
        self.current = value
        self.render()
    
    def render(self) -> None:
        """渲染进度条"""
        if self.total == 0:
            percent = 100
        else:
            percent = int(100 * self.current / self.total)
        
        filled = int(self.width * self.current / self.total) if self.total > 0 else 0
        bar = '=' * filled + '-' * (self.width - filled)
        
        parts = []
        if self.desc:
            parts.append(self.desc)
        
        parts.append(f"[{bar}]")
        
        if self.show_percent:
            parts.append(f"{percent}%")
        
        if self.show_count:
            parts.append(f"{self.current}/{self.total}")
        
        elapsed = time.time() - self._start_time
        if elapsed > 0:
            rate = self.current / elapsed
            parts.append(f"{rate:.1f}it/s")
        
        line = ' '.join(parts)
        sys.stdout.write('\r' + line)
        sys.stdout.flush()
        
        if self.current >= self.total:
            sys.stdout.write('\n')
    
    def finish(self) -> None:
        """完成"""
        self.current = self.total
        self.render()


class Spinner:
    """
    旋转器
    """
    
    def __init__(self, desc: str = ''):
        self.desc = desc
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current = 0
        self._running = False
    
    def start(self) -> None:
        """开始"""
        self._running = True
        self._spin()
    
    def _spin(self) -> None:
        """旋转"""
        if not self._running:
            return
        
        frame = self.frames[self.current % len(self.frames)]
        line = f"\r{frame} {self.desc}" if self.desc else f"\r{frame}"
        sys.stdout.write(line)
        sys.stdout.flush()
        self.current += 1
        
        if self._running:
            time.sleep(0.1)
    
    def stop(self) -> None:
        """停止"""
        self._running = False
        sys.stdout.write('\r' + ' ' * (len(self.desc) + 3) + '\r')
        sys.stdout.flush()


def progress_callback(
    iterable,
    desc: str = '',
    total: int = None,
):
    """
    进度回调迭代器
    
    Usage:
        for item in progress_callback(items, "Processing"):
            process(item)
    """
    if total is None:
        try:
            total = len(iterable)
        except TypeError:
            total = None
    
    bar = ProgressBar(total or 100, desc=desc, show_count=False)
    
    for i, item in enumerate(iterable):
        yield item
        bar.set(i + 1)
    
    bar.finish()


# 导出
__all__ = [
    "ProgressBar",
    "Spinner",
    "progress_callback",
]
