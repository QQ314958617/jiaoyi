"""
CompletionCache - 完成缓存
基于 Claude Code completion_cache.ts 设计

完成缓存工具。
"""
import time
import hashlib
from typing import Any, Optional


class CompletionCache:
    """
    完成缓存
    
    用于缓存LLM调用结果。
    """
    
    def __init__(self, ttl: float = 3600):
        """
        Args:
            ttl: 生存时间（秒），默认1小时
        """
        self._cache = {}
        self._ttl = ttl
    
    def _make_key(self, prompt: str, **kwargs) -> str:
        """生成缓存键"""
        data = prompt + str(sorted(kwargs.items()))
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, prompt: str, **kwargs) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
            
        Returns:
            缓存的结果或None
        """
        key = self._make_key(prompt, **kwargs)
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # 检查过期
        if time.time() - entry["time"] > self._ttl:
            del self._cache[key]
            return None
        
        return entry["result"]
    
    def set(self, prompt: str, result: Any, **kwargs):
        """
        设置缓存
        """
        key = self._make_key(prompt, **kwargs)
        self._cache[key] = {
            "result": result,
            "time": time.time()
        }
    
    def invalidate(self, prompt: str = None, **kwargs):
        """
        使缓存失效
        
        Args:
            prompt: 提示词（None表示全部）
        """
        if prompt is None:
            self._cache.clear()
            return
        
        key = self._make_key(prompt, **kwargs)
        self._cache.pop(key, None)
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
    
    def size(self) -> int:
        """缓存条目数"""
        return len(self._cache)


# 全局缓存实例
_default_cache = CompletionCache()


def get() -> Any:
    """获取全局缓存"""
    return _default_cache


def clear():
    """清空全局缓存"""
    _default_cache.clear()


# 导出
__all__ = [
    "CompletionCache",
    "get",
    "clear",
]
