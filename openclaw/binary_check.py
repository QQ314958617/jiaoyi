"""
Binary Check - 二进制检查
基于 Claude Code binaryCheck.ts 设计

检查系统命令是否可用。
"""
import threading
from typing import Optional

from .which import which


# 缓存
_binary_cache: dict[str, bool] = {}
_binary_cache_lock = threading.Lock()


def is_binary_installed(command: str) -> bool:
    """
    检查命令是否已安装
    
    Args:
        command: 命令名
        
    Returns:
        是否可用
    """
    global _binary_cache
    
    if not command or not command.strip():
        return False
    
    command = command.strip()
    
    # 检查缓存
    with _binary_cache_lock:
        if command in _binary_cache:
            return _binary_cache[command]
    
    # 使用which检查
    result = which(command)
    exists = result is not None
    
    # 缓存结果
    with _binary_cache_lock:
        _binary_cache[command] = exists
    
    return exists


def clear_binary_cache() -> None:
    """清空二进制检查缓存"""
    global _binary_cache
    with _binary_cache_lock:
        _binary_cache.clear()


# 导出
__all__ = [
    "is_binary_installed",
    "clear_binary_cache",
]
