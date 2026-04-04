"""
Console - 控制台工具
基于 Claude Code console.ts 设计

控制台输出工具。
"""
import sys
from typing import Any


def log(*args, **kwargs) -> None:
    """标准输出"""
    print(*args, **kwargs)


def error(*args, **kwargs) -> None:
    """错误输出"""
    print(*args, file=sys.stderr, **kwargs)


def warn(*args, **kwargs) -> None:
    """警告输出"""
    print(*args, file=sys.stderr, **kwargs)


def info(*args, **kwargs) -> None:
    """信息输出"""
    print(*args, **kwargs)


def debug(*args, **kwargs) -> None:
    """调试输出"""
    import os
    if os.environ.get('DEBUG'):
        print(*args, **kwargs)


def print_table(data: list, headers: list = None) -> None:
    """
    打印表格
    
    Args:
        data: 数据列表
        headers: 表头
    """
    if not data:
        return
    
    # 获取每列最大宽度
    if headers:
        rows = [headers] + [[str(item) for item in row] for row in data]
    else:
        rows = [[str(item) for item in row] for row in data]
    
    col_widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]
    
    # 格式化行
    for row in rows:
        line = ' | '.join(
            str(row[i]).ljust(col_widths[i]) for i in range(len(row))
        )
        print(line)


def print_json(obj: Any, indent: int = 2) -> None:
    """打印JSON"""
    import json
    print(json.dumps(obj, indent=indent, ensure_ascii=False))


def print_list(items: list, prefix: str = '  ') -> None:
    """打印列表"""
    for item in items:
        print(f"{prefix}• {item}")


def print_tree(data: dict, indent: int = 0) -> None:
    """打印树形结构"""
    prefix = '  ' * indent
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                print(f"{prefix}├── {key}:")
                print_tree(value, indent + 1)
            else:
                print(f"{prefix}├── {key}: {value}")
    else:
        print(f"{prefix}└── {data}")


class Logger:
    """
    日志记录器
    """
    
    def __init__(
        self,
        name: str = '',
        level: str = 'info',
    ):
        self.name = name
        self.level = level
    
    def _log(self, level: str, *args, **kwargs) -> None:
        prefix = f"[{level.upper()}]"
        if self.name:
            prefix += f"[{self.name}]"
        
        print(prefix, *args, **kwargs)
    
    def debug(self, *args, **kwargs) -> None:
        if self.level == 'debug':
            self._log('debug', *args, **kwargs)
    
    def info(self, *args, **kwargs) -> None:
        if self.level in ('debug', 'info'):
            self._log('info', *args, **kwargs)
    
    def warn(self, *args, **kwargs) -> None:
        if self.level in ('debug', 'info', 'warn'):
            self._log('warn', *args, **kwargs)
    
    def error(self, *args, **kwargs) -> None:
        self._log('error', *args, **kwargs)


# 导出
__all__ = [
    "log",
    "error",
    "warn",
    "info",
    "debug",
    "print_table",
    "print_json",
    "print_list",
    "print_tree",
    "Logger",
]
