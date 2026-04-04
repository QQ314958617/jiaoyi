"""
Serializer - 序列化
基于 Claude Code serializer.ts 设计

对象序列化工具。
"""
import json
from typing import Any, Callable, Dict, List, Optional


def to_json(obj: Any, indent: int = None) -> str:
    """
    序列化为JSON
    
    Args:
        obj: 对象
        indent: 缩进
        
    Returns:
        JSON字符串
    """
    return json.dumps(obj, indent=indent, ensure_ascii=False)


def from_json(text: str) -> Any:
    """
    从JSON反序列化
    
    Args:
        text: JSON字符串
        
    Returns:
        对象
    """
    return json.loads(text)


def to_json_file(obj: Any, path: str, indent: int = 2) -> None:
    """
    序列化到文件
    
    Args:
        obj: 对象
        path: 文件路径
        indent: 缩进
    """
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)


def from_json_file(path: str) -> Any:
    """
    从文件反序列化
    
    Args:
        path: 文件路径
        
    Returns:
        对象
    """
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def pick_fields(obj: dict, fields: List[str]) -> dict:
    """
    只保留指定字段
    
    Args:
        obj: 对象
        fields: 字段列表
        
    Returns:
        新对象
    """
    return {k: v for k, v in obj.items() if k in fields}


def omit_fields(obj: dict, fields: List[str]) -> dict:
    """
    排除指定字段
    
    Args:
        obj: 对象
        fields: 要排除的字段列表
        
    Returns:
        新对象
    """
    return {k: v for k, v in obj.items() if k not in fields}


def flatten(obj: dict, separator: str = '.') -> dict:
    """
    扁平化嵌套字典
    
    Args:
        obj: 嵌套字典
        separator: 键分隔符
        
    Returns:
        扁平字典
    """
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


def unflatten(obj: dict, separator: str = '.') -> dict:
    """
    反扁平化字典
    
    Args:
        obj: 扁平字典
        separator: 键分隔符
        
    Returns:
        嵌套字典
    """
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


class Serializer:
    """
    序列化器
    
    支持自定义字段过滤和转换。
    """
    
    def __init__(
        self,
        include: List[str] = None,
        exclude: List[str] = None,
        rename: Dict[str, str] = None,
        transform: Dict[str, Callable] = None,
    ):
        """
        Args:
            include: 只包含的字段
            exclude: 排除的字段
            rename: 字段重命名
            transform: 字段转换函数
        """
        self._include = include
        self._exclude = exclude or []
        self._rename = rename or {}
        self._transform = transform or {}
    
    def serialize(self, obj: dict) -> dict:
        """序列化对象"""
        # 过滤
        if self._include:
            result = pick_fields(obj, self._include)
        else:
            result = omit_fields(obj, self._exclude)
        
        # 重命名
        if self._rename:
            result = {
                self._rename.get(k, k): v
                for k, v in result.items()
            }
        
        # 转换
        for field, fn in self._transform.items():
            if field in result:
                result[field] = fn(result[field])
        
        return result
    
    def deserialize(self, data: dict) -> dict:
        """反序列化对象"""
        # 反转换
        result = dict(data)
        for field, fn in self._transform.items():
            if field in result:
                try:
                    result[field] = fn(result[field])
                except Exception:
                    pass
        
        # 反重命名
        if self._rename:
            inverse_rename = {v: k for k, v in self._rename.items()}
            result = {
                inverse_rename.get(k, k): v
                for k, v in result.items()
            }
        
        return result


# 导出
__all__ = [
    "to_json",
    "from_json",
    "to_json_file",
    "from_json_file",
    "pick_fields",
    "omit_fields",
    "flatten",
    "unflatten",
    "Serializer",
]
