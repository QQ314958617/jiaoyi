"""
StatsCache - 统计缓存
基于 Claude Code stats_cache.ts 设计

统计数据缓存工具。
"""
import time
from typing import Dict, Any, Optional


class StatsCache:
    """
    统计数据缓存
    """
    
    def __init__(self, ttl: float = 60):
        """
        Args:
            ttl: 生存时间（秒）
        """
        self._data: Dict[str, Dict] = {}
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取统计数据"""
        if key not in self._data:
            return None
        
        entry = self._data[key]
        
        # 检查过期
        if time.time() - entry["time"] > self._ttl:
            del self._data[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any):
        """设置统计数据"""
        self._data[key] = {
            "value": value,
            "time": time.time()
        }
    
    def increment(self, key: str, delta: float = 1) -> float:
        """递增"""
        current = self.get(key) or 0
        new_value = current + delta
        self.set(key, new_value)
        return new_value
    
    def decrement(self, key: str, delta: float = 1) -> float:
        """递减"""
        current = self.get(key) or 0
        new_value = current - delta
        self.set(key, new_value)
        return new_value
    
    def clear(self):
        """清空"""
        self._data.clear()
    
    def keys(self) -> list:
        """获取所有键"""
        return list(self._data.keys())


# 全局实例
_stats_cache = StatsCache()


def get_stats(key: str) -> Optional[Any]:
    """获取统计"""
    return _stats_cache.get(key)


def set_stats(key: str, value: Any):
    """设置统计"""
    _stats_cache.set(key, value)


def increment(key: str, delta: float = 1) -> float:
    """递增"""
    return _stats_cache.increment(key, delta)


def decrement(key: str, delta: float = 1) -> float:
    """递减"""
    return _stats_cache.decrement(key, delta)


def clear():
    """清空所有统计"""
    _stats_cache.clear()


# 导出
__all__ = [
    "StatsCache",
    "get_stats",
    "set_stats",
    "increment",
    "decrement",
    "clear",
]
