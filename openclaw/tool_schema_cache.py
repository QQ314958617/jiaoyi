"""
ToolSchemaCache - 工具Schema缓存
基于 Claude Code tool_schema_cache.ts 设计

工具Schema缓存工具。
"""
import time
import json
from typing import Any, Dict, Optional


class ToolSchemaCache:
    """
    工具Schema缓存
    """
    
    def __init__(self, ttl: float = 3600):
        """
        Args:
            ttl: 生存时间（秒）
        """
        self._cache: Dict[str, Dict] = {}
        self._ttl = ttl
    
    def get(self, tool_name: str) -> Optional[Dict]:
        """
        获取Schema
        
        Returns:
            Schema或None
        """
        if tool_name not in self._cache:
            return None
        
        entry = self._cache[tool_name]
        
        # 检查过期
        if time.time() - entry["time"] > self._ttl:
            del self._cache[tool_name]
            return None
        
        return entry["schema"]
    
    def set(self, tool_name: str, schema: Dict):
        """设置Schema"""
        self._cache[tool_name] = {
            "schema": schema,
            "time": time.time(),
        }
    
    def has(self, tool_name: str) -> bool:
        """是否存在"""
        return self.get(tool_name) is not None
    
    def invalidate(self, tool_name: str = None):
        """使缓存失效"""
        if tool_name:
            self._cache.pop(tool_name, None)
        else:
            self._cache.clear()
    
    def clear(self):
        """清空"""
        self._cache.clear()
    
    def size(self) -> int:
        """缓存数量"""
        return len(self._cache)


# 全局缓存
_cache = ToolSchemaCache()


def get_cache() -> ToolSchemaCache:
    """获取全局缓存"""
    return _cache


def get(tool_name: str) -> Optional[Dict]:
    """获取Schema"""
    return _cache.get(tool_name)


def set_(tool_name: str, schema: Dict):
    """设置Schema"""
    _cache.set(tool_name, schema)


def invalidate(tool_name: str = None):
    """使缓存失效"""
    _cache.invalidate(tool_name)


# 导出
__all__ = [
    "ToolSchemaCache",
    "get_cache",
    "get",
    "set_",
    "invalidate",
]
