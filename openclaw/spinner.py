"""
Spinner - 加载动画
基于 Claude Code spinner.ts 设计

加载动画工具。
"""
import sys
import time


class Spinner:
    """加载动画"""
    
    FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    def __init__(self, message: str = "Loading"):
        self.message = message
        self._running = False
        self._frame = 0
    
    def start(self):
        """开始动画"""
        self._running = True
        self._spin()
    
    def stop(self):
        """停止动画"""
        self._running = False
        print('\r' + ' ' * (len(self.message) + 10) + '\r', end='')
    
    def _spin(self):
        """转动一帧"""
        if not self._running:
            return
        
        frame = self.FRAMES[self._frame % len(self.FRAMES)]
        print(f'\r{frame} {self.message}', end='', flush=True)
        self._frame += 1
        
        if self._running:
            import threading
            threading.Timer(0.1, self._spin).start()


def spin(duration: float = 1.0, message: str = "Loading"):
    """
    显示指定时长的加载动画
    
    Args:
        duration: 时长（秒）
        message: 消息
    """
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    start = time.time()
    i = 0
    
    while time.time() - start < duration:
        frame = frames[i % len(frames)]
        print(f'\r{frame} {message}', end='', flush=True)
        i += 1
        time.sleep(0.1)
    
    print('\r' + ' ' * (len(message) + 10) + '\r', end='')


# 导出
__all__ = [
    "Spinner",
    "spin",
]
