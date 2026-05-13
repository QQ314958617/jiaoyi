"""
统一缓存管理模块
替代原有三套混乱缓存（手动dict、lru_cache、openclaw cache）
"""
import time
import threading
from typing import Any, Optional


class TTLCache:
    """线程安全的 TTL 缓存"""

    def __init__(self, default_ttl: int = 30):
        self._store: dict = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，过期返回 None"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if time.time() - entry['time'] > entry['ttl']:
                return None
            return entry['data']

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        with self._lock:
            self._store[key] = {
                'data': data,
                'time': time.time(),
                'ttl': ttl if ttl is not None else self._default_ttl,
            }

    def get_or_none(self, key: str) -> tuple:
        """返回 (data, is_expired) — 即使过期也返回旧数据"""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None, True
            expired = time.time() - entry['time'] > entry['ttl']
            return entry['data'], expired

    def invalidate(self, key: str) -> None:
        """删除缓存"""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._store.clear()


# 全局缓存实例
cache = TTLCache(default_ttl=30)
