"""
Filter - 过滤器
基于 Claude Code filter.ts 设计

过滤器工具。
"""
from typing import Any, Callable, List, Dict


def filter_items(items: List, predicate: Callable) -> List:
    """
    过滤
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        过滤后的列表
    """
    return [item for item in items if predicate(item)]


def reject(items: List, predicate: Callable) -> List:
    """
    拒绝
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        不满足条件的列表
    """
    return [item for item in items if not predicate(item)]


def find(items: List, predicate: Callable) -> Any:
    """
    查找
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        第一个满足条件的元素或None
    """
    for item in items:
        if predicate(item):
            return item
    return None


def find_index(items: List, predicate: Callable) -> int:
    """
    查找索引
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        索引或-1
    """
    for i, item in enumerate(items):
        if predicate(item):
            return i
    return -1


def every(items: List, predicate: Callable) -> bool:
    """
    是否所有都满足
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        是否所有都满足
    """
    for item in items:
        if not predicate(item):
            return False
    return True


def some(items: List, predicate: Callable) -> bool:
    """
    是否有任意满足
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        是否存在满足条件的元素
    """
    for item in items:
        if predicate(item):
            return True
    return False


def none(items: List, predicate: Callable) -> bool:
    """
    是否都不满足
    
    Args:
        items: 列表
        predicate: 谓词
        
    Returns:
        是否所有都不满足
    """
    return not some(items, predicate)


def where(items: List[Dict], criteria: Dict) -> List:
    """
    按条件过滤字典列表
    
    Args:
        items: 字典列表
        criteria: 条件
        
    Returns:
        匹配的字典列表
    """
    result = []
    for item in items:
        match = True
        for key, value in criteria.items():
            if item.get(key) != value:
                match = False
                break
        if match:
            result.append(item)
    return result


# 导出
__all__ = [
    "filter_items",
    "reject",
    "find",
    "find_index",
    "every",
    "some",
    "none",
    "where",
]
