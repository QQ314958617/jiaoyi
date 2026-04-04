"""
Box - 边框
基于 Claude Code box.ts 设计

边框/框工具。
"""


def box(text: str, padding: int = 0) -> str:
    """
    简单边框
    
    Args:
        text: 内容
        padding: 内边距
        
    Returns:
        带边框的文本
    """
    lines = text.split('\n')
    max_len = max(len(line) for line in lines)
    
    pad = ' ' * padding
    width = max_len + padding * 2
    
    top = '┌' + '─' * (width + 2) + '┐'
    bottom = '└' + '─' * (width + 2) + '┘'
    
    middle = []
    for line in lines:
        content = pad + line + ' ' * (max_len - len(line)) + pad
        middle.append('│ ' + content + ' │')
    
    return '\n'.join([top] + middle + [bottom])


def rounded_box(text: str) -> str:
    """圆角边框"""
    lines = text.split('\n')
    max_len = max(len(line) for line in lines)
    width = max_len
    
    top = '╭' + '─' * (width + 2) + '╮'
    bottom = '╰' + '─' * (width + 2) + '╯'
    
    middle = []
    for line in lines:
        middle.append('│ ' + line + ' ' * (max_len - len(line)) + ' │')
    
    return '\n'.join([top] + middle + [bottom])


def double_box(text: str) -> str:
    """双线边框"""
    lines = text.split('\n')
    max_len = max(len(line) for line in lines)
    width = max_len
    
    top = '╔' + '═' * (width + 2) + '╗'
    bottom = '╚' + '═' * (width + 2) + '╝'
    
    middle = []
    for line in lines:
        middle.append('║ ' + line + ' ' * (max_len - len(line)) + ' ║')
    
    return '\n'.join([top] + middle + [bottom])


def info_box(text: str) -> str:
    """信息框"""
    return box(text, padding=1)


def success_box(text: str) -> str:
    """成功框"""
    return box(text, padding=1)


def warning_box(text: str) -> str:
    """警告框"""
    return box(text, padding=1)


def error_box(text: str) -> str:
    """错误框"""
    return box(text, padding=1)


def header(text: str, width: int = None) -> str:
    """
    标题头
    
    Args:
        text: 标题文本
        width: 总宽度
        
    Returns:
        标题字符串
    """
    if width is None:
        width = len(text) + 4
    
    return '┌' + '─' * width + '┐\n│  ' + text + ' ' * (width - len(text) - 2) + ' │\n└' + '─' * width + '┘'


# 导出
__all__ = [
    "box",
    "rounded_box",
    "double_box",
    "info_box",
    "success_box",
    "warning_box",
    "error_box",
    "header",
]
