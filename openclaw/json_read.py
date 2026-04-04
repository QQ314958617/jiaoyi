"""
JsonRead - JSON读取
基于 Claude Code json_read.ts 设计

JSON读取工具。
"""
import json
from typing import Any, Dict


def read(path: str) -> Any:
    """
    读取JSON文件
    
    Args:
        path: 文件路径
        
    Returns:
        解析后的对象
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse(text: str) -> Any:
    """
    解析JSON字符串
    
    Args:
        text: JSON字符串
        
    Returns:
        解析后的对象
    """
    return json.loads(text)


def read_safe(path: str, default: Any = None) -> Any:
    """
    安全读取JSON（失败返回默认值）
    """
    try:
        return read(path)
    except (json.JSONDecodeError, FileNotFoundError, IOError):
        return default


def parse_safe(text: str, default: Any = None) -> Any:
    """
    安全解析JSON（失败返回默认值）
    """
    try:
        return parse(text)
    except json.JSONDecodeError:
        return default


def get(data: Dict, key: str, default: Any = None) -> Any:
    """
    安全获取嵌套值
    
    Args:
        data: {"a": {"b": 1}}
        key: "a.b"
        default: 默认值
    """
    keys = key.split('.')
    value = data
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def has(data: Dict, key: str) -> bool:
    """
    检查键是否存在
    
    Args:
        data: {"a": {"b": 1}}
        key: "a.b"
    """
    keys = key.split('.')
    value = data
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return False
    
    return True


def set_nested(data: Dict, key: str, value: Any) -> Dict:
    """
    设置嵌套值
    
    Args:
        data: 原始字典
        key: "a.b.c"
        value: 要设置的值
        
    Returns:
        新字典
    """
    keys = key.split('.')
    result = dict(data)
    current = result
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
    return result


# 导出
__all__ = [
    "read",
    "parse",
    "read_safe",
    "parse_safe",
    "get",
    "has",
    "set_nested",
]
