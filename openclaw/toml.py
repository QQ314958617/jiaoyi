"""
TOML - TOML解析
基于 Claude Code toml.ts 设计

TOML工具。
"""
from typing import Any


def parse(toml_str: str) -> Any:
    """
    解析TOML
    
    Args:
        toml_str: TOML字符串
        
    Returns:
        Python对象
    """
    import tomli
    return tomli.loads(toml_str)


def dump(obj: Any) -> str:
    """
    转为TOML字符串
    
    Args:
        obj: Python对象
        
    Returns:
        TOML字符串
    """
    import tomli_w as tomli
    return tomli.dumps(obj)


def load(path: str) -> Any:
    """
    从文件加载TOML
    
    Args:
        path: 文件路径
        
    Returns:
        Python对象
    """
    import tomli
    with open(path, 'rb') as f:
        return tomli.load(f)


def save(obj: Any, path: str) -> None:
    """
    保存为TOML文件
    
    Args:
        obj: Python对象
        path: 文件路径
    """
    import tomli_w as tomli
    with open(path, 'wb') as f:
        tomli.dump(obj, f)


# 导出
__all__ = [
    "parse",
    "dump",
    "load",
    "save",
]
