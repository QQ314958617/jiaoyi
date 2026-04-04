"""
Keyboard - 键盘
基于 Claude Code keyboard.ts 设计

键盘工具。
"""


# 功能键
KEY_UP = '\033[A'
KEY_DOWN = '\033[B'
KEY_RIGHT = '\033[C'
KEY_LEFT = '\033[D'
KEY_ENTER = '\n'
KEY_ESCAPE = '\033'
KEY_TAB = '\t'
KEY_BACKSPACE = '\x7f'
KEY_DELETE = '\033[3~'
KEY_HOME = '\033[H'
KEY_END = '\033[F'
KEY_PAGE_UP = '\033[5~'
KEY_PAGE_DOWN = '\033[6~'


def is_arrow_key(key: str) -> bool:
    """是否为方向键"""
    return key in (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT)


def is_function_key(key: str) -> bool:
    """是否为功能键"""
    return key.startswith('\033[')


def read_char() -> str:
    """读取单个字符（Unix）"""
    import sys
    import tty
    import termios
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return ch


def read_line(prompt: str = "") -> str:
    """读取一行"""
    if prompt:
        print(prompt, end='', flush=True)
    return input()


class KeyHandler:
    """按键处理器"""
    
    def __init__(self):
        self._handlers = {}
    
    def on(self, key: str, handler: callable):
        """注册按键处理"""
        self._handlers[key] = handler
    
    def handle(self, key: str):
        """处理按键"""
        if key in self._handlers:
            self._handlers[key]()
    
    def on_arrow_up(self, handler: callable):
        self.on(KEY_UP, handler)
    
    def on_arrow_down(self, handler: callable):
        self.on(KEY_DOWN, handler)
    
    def on_enter(self, handler: callable):
        self.on(KEY_ENTER, handler)
    
    def on_escape(self, handler: callable):
        self.on(KEY_ESCAPE, handler)


# 导出
__all__ = [
    "KEY_UP", "KEY_DOWN", "KEY_RIGHT", "KEY_LEFT",
    "KEY_ENTER", "KEY_ESCAPE", "KEY_TAB", "KEY_BACKSPACE",
    "KEY_DELETE", "KEY_HOME", "KEY_END", "KEY_PAGE_UP", "KEY_PAGE_DOWN",
    "is_arrow_key", "is_function_key",
    "read_char", "read_line",
    "KeyHandler",
]
