"""
Transform - 变换
基于 Claude Code transform.ts 设计

数据变换工具。
"""
from typing import Any, Callable, Dict, List


def map_items(items: List, fn: Callable) -> List:
    """
    映射
    
    Args:
        items: 列表
        fn: 变换函数
        
    Returns:
        变换后的列表
    """
    return [fn(item) for item in items]


def flat_map(items: List, fn: Callable) -> List:
    """
    扁平映射
    
    Args:
        items: 列表
        fn: 变换函数（返回列表）
        
    Returns:
        扁平化结果
    """
    result = []
    for item in items:
        result.extend(fn(item))
    return result


def pluck(items: List[Dict], key: str) -> List:
    """
    提取键值
    
    Args:
        items: 字典列表
        key: 键名
        
    Returns:
        值列表
    """
    return [item.get(key) for item in items if isinstance(item, dict)]


def property_map(items: List, source_key: str, target_key: str = None) -> List[Dict]:
    """
    属性映射
    
    Args:
        items: 字典列表
        source_key: 源键
        target_key: 目标键（默认同source_key）
        
    Returns:
        映射后的字典列表
    """
    if target_key is None:
        target_key = source_key
    
    return [
        {**(item if isinstance(item, dict) else {}), target_key: item.get(source_key) if isinstance(item, dict) else getattr(item, source_key, None)}
        for item in items
    ]


def key_by(items: List[Dict], key: str) -> Dict:
    """
    以键索引
    
    Args:
        items: 字典列表
        key: 键名
        
    Returns:
        { key_value: item }
    """
    return {item.get(key): item for item in items if isinstance(item, dict) and key in item}


def sort_by(items: List, key: str, reverse: bool = False) -> List:
    """
    按键排序
    
    Args:
        items: 字典列表
        key: 键名
        reverse: 是否降序
        
    Returns:
        排序后的列表
    """
    return sorted(items, key=lambda x: x.get(key) if isinstance(x, dict) else getattr(x, key, None), reverse=reverse)


def uniq_by(items: List, key: str) -> List:
    """
    按键去重
    
    Args:
        items: 字典列表
        key: 键名
        
    Returns:
        去重后的列表
    """
    seen = set()
    result = []
    for item in items:
        if isinstance(item, dict) and key in item:
            val = item[key]
            if val not in seen:
                seen.add(val)
                result.append(item)
    return result


def assoc(items: List[Dict], key: str, value: Any) -> List[Dict]:
    """
    关联
    
    Args:
        items: 字典列表
        key: 键
        value: 值或函数
        
    Returns:
        新列表
    """
    result = []
    for item in items:
        new_item = dict(item) if isinstance(item, dict) else {}
        if callable(value):
            new_item[key] = value(item)
        else:
            new_item[key] = value
        result.append(new_item)
    return result


def dissoc(items: List[Dict], key: str) -> List[Dict]:
    """
    解除关联
    
    Args:
        items: 字典列表
        key: 键
        
    Returns:
        新列表
    """
    return [{k: v for k, v in (item.items() if isinstance(item, dict) else {}) if k != key} for item in items]


# 导出
__all__ = [
    "map_items",
    "flat_map",
    "pluck",
    "property_map",
    "key_by",
    "sort_by",
    "uniq_by",
    "assoc",
    "dissoc",
]
