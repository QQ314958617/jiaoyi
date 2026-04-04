"""
KeyboardShortcuts - 键盘快捷键
基于 Claude Code keyboard_shortcuts.ts 设计

键盘快捷键工具。
"""
import sys
import tty
import termios
from typing import Callable, Dict, Optional


# ANSI转义码
KEY_UP = '\033[A'
KEY_DOWN = '\033[B'
KEY_RIGHT = '\033[C'
KEY_LEFT = '\033[D'
KEY_ENTER = '\n'
KEY_ESCAPE = '\033'
KEY_TAB = '\t'
KEY_BACKSPACE = '\127'
KEY_DELETE = '\033[3~'
KEY_HOME = '\033[H'
KEY_END = '\033[F'
KEY_PAGE_UP = '\033[5~'
KEY_PAGE_DOWN = '\033[6~'


class KeyboardShortcuts:
    """
    键盘快捷键处理器
    """
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._running = False
    
    def on(self, key: str, handler: Callable):
        """注册快捷键"""
        self._handlers[key] = handler
    
    def on_ctrl_c(self, handler: Callable):
        """Ctrl+C"""
        self.on('ctrl-c', handler)
    
    def on_ctrl_d(self, handler: Callable):
        """Ctrl+D"""
        self.on('ctrl-d', handler)
    
    def on_ctrl_z(self, handler: Callable):
        """Ctrl+Z"""
        self.on('ctrl-z', handler)
    
    def on_arrow_up(self, handler: Callable):
        """上箭头"""
        self.on(KEY_UP, handler)
    
    def on_arrow_down(self, handler: Callable):
        """下箭头"""
        self.on(KEY_DOWN, handler)
    
    def on_arrow_left(self, handler: Callable):
        """左箭头"""
        self.on(KEY_LEFT, handler)
    
    def on_arrow_right(self, handler: Callable):
        """右箭头"""
        self.on(KEY_RIGHT, handler)
    
    def on_enter(self, handler: Callable):
        """回车"""
        self.on(KEY_ENTER, handler)
    
    def on_escape(self, handler: Callable):
        """ESC"""
        self.on(KEY_ESCAPE, handler)
    
    def handle(self, key: str) -> bool:
        """处理按键"""
        if key in self._handlers:
            self._handlers[key]()
            return True
        if 'ctrl-c' in self._handlers and key == 'ctrl-c':
            self._handlers['ctrl-c']()
            return True
        return False
    
    def read_key(self) -> str:
        """读取按键"""
        # Unix终端设置
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
            
            # 检查是否是转义序列
            if key == '\033':
                # 读取后续字符
                if sys.stdin.read(1) == '[':
                    key += '['
                    next_char = sys.stdin.read(1)
                    key += next_char
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        return key
    
    def listen(self, until: str = None):
        """监听按键"""
        self._running = True
        
        while self._running:
            key = self.read_key()
            
            if key == until:
                break
            
            self.handle(key)


# 全局实例
_shortcuts = KeyboardShortcuts()


def on(key: str, handler: Callable):
    """注册快捷键"""
    _shortcuts.on(key, handler)


def listen(until: str = None):
    """监听"""
    _shortcuts.listen(until)


# 导出
__all__ = [
    "KEY_UP",
    "KEY_DOWN",
    "KEY_LEFT",
    "KEY_RIGHT",
    "KEY_ENTER",
    "KEY_ESCAPE",
    "KEY_TAB",
    "KEY_BACKSPACE",
    "KEY_DELETE",
    "KEY_HOME",
    "KEY_END",
    "KEY_PAGE_UP",
    "KEY_PAGE_DOWN",
    "KeyboardShortcuts",
    "on",
    "listen",
]
