"""
Window - 窗口
基于 Claude Code window.ts 设计

窗口函数工具。
"""
from typing import Any, Callable, List


def window(items: List, size: int, step: int = 1) -> List[List]:
    """
    窗口切片
    
    Args:
        items: 列表
        size: 窗口大小
        step: 步长
        
    Returns:
        窗口列表
    """
    if size <= 0 or step <= 0:
        return []
    
    result = []
    for i in range(0, len(items), step):
        window_items = items[i:i+size]
        if len(window_items) == size:
            result.append(window_items)
        elif len(window_items) > 0 and len(window_items) < size:
            result.append(window_items)
    
    return result


def sliding_window(items: List, size: int) -> List[List]:
    """
    滑动窗口
    
    Args:
        items: 列表
        size: 窗口大小
        
    Returns:
        滑动窗口列表
    """
    return window(items, size, 1)


def moving_average(values: List, window_size: int) -> List[float]:
    """
    移动平均
    
    Args:
        values: 数值列表
        window_size: 窗口大小
        
    Returns:
        移动平均值列表
    """
    if len(values) < window_size:
        return []
    
    result = []
    window = values[:window_size]
    result.append(sum(window) / window_size)
    
    for i in range(window_size, len(values)):
        window = values[i-window_size+1:i+1]
        result.append(sum(window) / window_size)
    
    return result


def window_by(items: List, key_fn: Callable, max_size: int) -> List[List]:
    """
    按键分窗口
    
    Args:
        items: 列表
        key_fn: 键函数
        max_size: 最大窗口大小
        
    Returns:
        窗口列表
    """
    result = []
    current = []
    last_key = None
    
    for item in items:
        key = key_fn(item)
        
        if last_key is not None and key != last_key:
            if current:
                result.append(current)
            current = [item]
            last_key = key
        else:
            current.append(item)
            last_key = key
            
            if len(current) >= max_size:
                result.append(current)
                current = []
    
    if current:
        result.append(current)
    
    return result


# 导出
__all__ = [
    "window",
    "sliding_window",
    "moving_average",
    "window_by",
]
