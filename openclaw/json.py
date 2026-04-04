"""
JSON - JSON工具
基于 Claude Code json.ts 设计

JSON处理增强工具。
"""
import json
from typing import Any, Callable, Dict, List, Optional


def parse(text: str, default: Any = None) -> Any:
    """
    解析JSON
    
    Args:
        text: JSON字符串
        default: 解析失败时的默认值
        
    Returns:
        解析后的对象
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def stringify(obj: Any, indent: int = None) -> str:
    """
    序列化为JSON
    
    Args:
        obj: 对象
        indent: 缩进
        
    Returns:
        JSON字符串
    """
    return json.dumps(obj, indent=indent, ensure_ascii=False)


def pretty(obj: Any) -> str:
    """美化输出"""
    return json.dumps(obj, indent=2, ensure_ascii=False)


def is_valid_json(text: str) -> bool:
    """检查是否为有效JSON"""
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def merge_json(obj1: dict, obj2: dict) -> dict:
    """
    合并JSON对象
    
    Args:
        obj1: 基础对象
        obj2: 合并对象
        
    Returns:
        合并后的对象
    """
    result = dict(obj1)
    
    for key, value in obj2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json(result[key], value)
        else:
            result[key] = value
    
    return result


def pick_json_fields(obj: dict, fields: List[str]) -> dict:
    """选取字段"""
    return {k: v for k, v in obj.items() if k in fields}


def omit_json_fields(obj: dict, fields: List[str]) -> dict:
    """排除字段"""
    return {k: v for k, v in obj.items() if k not in fields}


def flatten_json(obj: dict, separator: str = '.') -> dict:
    """扁平化嵌套JSON"""
    result = {}
    
    def _flatten(current: Any, prefix: str = ''):
        if isinstance(current, dict):
            for k, v in current.items():
                new_key = f"{prefix}{separator}{k}" if prefix else k
                _flatten(v, new_key)
        else:
            result[prefix] = current
    
    _flatten(obj)
    return result


def unflatten_json(obj: dict, separator: str = '.') -> dict:
    """反扁平化"""
    result = {}
    
    for flat_key, value in obj.items():
        keys = flat_key.split(separator)
        current = result
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    return result


class JSONCache:
    """JSON缓存"""
    
    def __init__(self, max_size: int = 100):
        self._cache: dict = {}
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存"""
        if len(self._cache) >= self._max_size:
            # 简单策略：清空一半
            keys = list(self._cache.keys())[:self._max_size // 2]
            for k in keys:
                del self._cache[k]
        
        self._cache[key] = value
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()


# 导出
__all__ = [
    "parse",
    "stringify",
    "pretty",
    "is_valid_json",
    "merge_json",
    "pick_json_fields",
    "omit_json_fields",
    "flatten_json",
    "unflatten_json",
    "JSONCache",
]
