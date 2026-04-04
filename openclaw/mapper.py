"""
Mapper - 映射器
基于 Claude Code mapper.ts 设计

数据映射工具。
"""
from typing import Any, Callable, Dict, List, TypeVar

T = TypeVar('T')
U = TypeVar('U')


def map_values(obj: dict, fn: Callable[[Any], Any]) -> dict:
    """
    映射字典值
    
    Args:
        obj: 字典
        fn: 值转换函数
        
    Returns:
        新字典
    """
    return {k: fn(v) for k, v in obj.items()}


def map_keys(obj: dict, fn: Callable[[str], str]) -> dict:
    """
    映射字典键
    
    Args:
        obj: 字典
        fn: 键转换函数
        
    Returns:
        新字典
    """
    return {fn(k): v for k, v in obj.items()}


def map_entries(obj: dict, fn: Callable[[str, Any], tuple]) -> dict:
    """
    映射字典条目
    
    Args:
        obj: 字典
        fn: (key, value) -> (new_key, new_value)
        
    Returns:
        新字典
    """
    return dict(fn(k, v) for k, v in obj.items())


def invert_map(obj: dict) -> dict:
    """
    反转字典
    
    Args:
        obj: 字典
        
    Returns:
        键值反转的字典
    """
    return {v: k for k, v in obj.items()}


def map_list(items: List[T], fn: Callable[[T], U]) -> List[U]:
    """
    映射列表
    
    Args:
        items: 列表
        fn: 转换函数
        
    Returns:
        转换后的列表
    """
    return [fn(item) for item in items]


def flat_map_list(items: List[List[T]]) -> List[T]:
    """
    扁平映射列表
    
    Args:
        items: 嵌套列表
        
    Returns:
        扁平化后的列表
    """
    return [item for sublist in items for item in sublist]


def group_by_map(items: List[T], key_fn: Callable[[T], str]) -> Dict[str, List[T]]:
    """
    分组映射
    
    Args:
        items: 列表
        key_fn: 分组键函数
        
    Returns:
        {组名: [项列表]}
    """
    result: Dict[str, List[T]] = {}
    
    for item in items:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    
    return result


def index_by(items: List[T], key_fn: Callable[[T], str]) -> Dict[str, T]:
    """
    按键索引
    
    Args:
        items: 列表
        key_fn: 键函数
        
    Returns:
        {键: 项}
    """
    return {key_fn(item): item for item in items}


def map_async(items: List[T], fn: Callable[[T], Any]) -> List[Any]:
    """
    异步映射（顺序）
    
    Args:
        items: 列表
        fn: 异步转换函数
        
    Returns:
        结果列表
    """
    import asyncio
    
    async def run():
        results = []
        for item in items:
            result = await fn(item)
            results.append(result)
        return results
    
    return asyncio.run(run())


def pipe_map(value: T, *fns: Callable) -> T:
    """
    管道映射
    
    Args:
        value: 初始值
        *fns: 转换函数列表
        
    Returns:
        最终结果
    """
    result = value
    for fn in fns:
        result = fn(result)
    return result


class Mapper:
    """
    映射器
    
    链式调用。
    """
    
    def __init__(self, data: Any):
        self._data = data
    
    def map(self, fn: Callable) -> "Mapper":
        """映射"""
        if isinstance(self._data, dict):
            self._data = map_values(self._data, fn)
        elif isinstance(self._data, list):
            self._data = map_list(self._data, fn)
        return self
    
    def flat_map(self, fn: Callable) -> "Mapper":
        """扁平映射"""
        if isinstance(self._data, list):
            self._data = flat_map_list([fn(item) for item in self._data])
        return self
    
    def filter(self, fn: Callable) -> "Mapper":
        """过滤"""
        if isinstance(self._data, list):
            self._data = [item for item in self._data if fn(item)]
        return self
    
    def value(self) -> Any:
        """获取值"""
        return self._data


# 导出
__all__ = [
    "map_values",
    "map_keys",
    "map_entries",
    "invert_map",
    "map_list",
    "flat_map_list",
    "group_by_map",
    "index_by",
    "map_async",
    "pipe_map",
    "Mapper",
]
