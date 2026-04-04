"""
Spinner - 加载动画
基于 Claude Code spinner.ts 设计

加载动画工具。
"""
import itertools
import time
from typing import Optional


class Spinner:
    """
    加载动画
    
    显示旋转的加载指示器。
    """
    
    def __init__(
        self,
        frames: str = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏",
        interval: float = 0.1,
        prefix: str = ""
    ):
        """
        Args:
            frames: 动画帧
            interval: 帧间隔（秒）
            prefix: 前缀文本
        """
        self._frames = frames
        self._interval = interval
        self._prefix = prefix
        self._index = 0
        self._running = False
        self._last_output = ""
    
    def spin(self) -> str:
        """
        下一帧
        
        Returns:
            当前帧
        """
        frame = self._frames[self._index % len(self._frames)]
        self._index += 1
        return f"{self._prefix}{frame}"
    
    def update(self) -> None:
        """更新显示"""
        import sys
        frame = self.spin()
        clear_len = len(self._last_output)
        output = f"\r{frame}{' ' * max(0, clear_len - len(frame))}"
        sys.stdout.write(output)
        sys.stdout.flush()
        self._last_output = frame
    
    def run(self, duration: float = None) -> None:
        """
        运行动画
        
        Args:
            duration: 持续时间（秒）
        """
        self._running = True
        start = time.time()
        
        while self._running:
            if duration and (time.time() - start) >= duration:
                break
            self.update()
            time.sleep(self._interval)
    
    def stop(self) -> None:
        """停止动画"""
        self._running = False
        import sys
        sys.stdout.write('\r' + ' ' * len(self._last_output) + '\r')
        sys.stdout.flush()


class MultiSpinner:
    """
    多行加载动画
    """
    
    def __init__(self):
        self._spinners = []
        self._running = False
    
    def add(self, id: str, frames: str = None) -> Spinner:
        """
        添加加载动画
        
        Args:
            id: 唯一标识
            frames: 动画帧
            
        Returns:
            Spinner实例
        """
        spinner = Spinner(frames=frames or "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
        spinner._id = id
        self._spinners.append(spinner)
        return spinner
    
    def remove(self, id: str) -> None:
        """移除加载动画"""
        self._spinners = [s for s in self._spinners if s._id != id]
    
    def spin(self) -> None:
        """更新所有动画"""
        import sys
        lines = []
        for spinner in self._spinners:
            lines.append(f"{spinner.spin()} {spinner._id}")
        
        output = '\n'.join(lines)
        sys.stdout.write('\033[K\r' + output + '\033[K\r')
        sys.stdout.flush()


# 内置加载动画
SPIFFY = Spinner("⠄⠆⠇⠈⠉⠊⠋⠌⠍⠎⠏⠐⠑⠒⠓⠔⠕⠖⠗⠘⠙⠚⠛⠜⠝⠞⠟⠠⠡⠢⠣⠤⠥⠦⠧⠨⠩⠪⠫⠬⠭⠮⠯⠰⠱⠲⠳⠴⠵⠶⠷⠸⠹⠺⠻⠼⠽⠾⠿")
DOTS = Spinner("⠋⠙⠹⠸⠼⠴")
ARROW = Spinner("◐◓◑◒")
SQUARES = Spinner("◢◣◤◥")
CIRCLES = Spinner("◓◐◑◒")
SQUARE_BOUNCE = Spinner("◫◧◨◩")


# 导出
__all__ = [
    "Spinner",
    "MultiSpinner",
    "SPIFFY",
    "DOTS",
    "ARROW",
    "SQUARES",
    "CIRCLES",
    "SQUARE_BOUNCE",
]
