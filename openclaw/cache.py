"""
OpenClaw Cache System
====================
Inspired by Claude Code's cache utilities.

缓存系统，支持：
1. 文件内容缓存（mtime 自动失效）
2. LRU 缓存（最近最少使用）
3. TTL 缓存（时间过期）
"""

from __future__ import annotations

import os, threading, time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

T = TypeVar('T')

# ============================================================================
# 缓存条目
# ============================================================================

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float = 0
    last_accessed: float = 0
    hit_count: int = 0
    file_mtime: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at == 0:
            self.created_at = time.time()
        if self.last_accessed == 0:
            self.last_accessed = time.time()

# ============================================================================
# 文件缓存
# ============================================================================

class FileReadCache:
    """文件内容缓存（mtime 自动失效）"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def _get_mtime(self, file_path: str) -> Optional[float]:
        try:
            return os.path.getmtime(file_path)
        except OSError:
            return None
    
    def read_file(self, file_path: str) -> str:
        mtime = self._get_mtime(file_path)
        current_mtime = mtime or 0
        
        with self._lock:
            cached = self._cache.get(file_path)
            if cached and cached.file_mtime == current_mtime:
                cached.last_accessed = time.time()
                cached.hit_count += 1
                self._hits += 1
                return cached.value
            self._misses += 1
        
        content = ""
        encoding = "utf-8"
        try:
            encoding = self._detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            content = content.replace('\r\n', '\n')
            
            with self._lock:
                if len(self._cache) >= self._max_size:
                    self._evict_lru()
                entry = CacheEntry(key=file_path, value=content, file_mtime=current_mtime)
                self._cache[file_path] = entry
        except (IOError, OSError) as e:
            raise FileNotFoundError(f"Cannot read {file_path}: {e}") from e
        
        return content
    
    def _detect_encoding(self, file_path: str) -> str:
        try:
            with open(file_path, 'rb') as f:
                raw = f.read(4096)
            if raw.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            try:
                raw.decode('utf-8')
                return 'utf-8'
            except:
                pass
            try:
                raw.decode('gbk')
                return 'gbk'
            except:
                pass
            return 'utf-8'
        except:
            return 'utf-8'
    
    def _evict_lru(self) -> None:
        if not self._cache:
            return
        oldest = min(self._cache.values(), key=lambda e: e.last_accessed)
        del self._cache[oldest.key]
    
    def invalidate(self, file_path: str) -> None:
        with self._lock:
            self._cache.pop(file_path, None)
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {"size": len(self._cache), "max_size": self._max_size,
                    "hits": self._hits, "misses": self._misses, "hit_rate": f"{hit_rate:.1%}"}

# ============================================================================
# LRU 缓存
# ============================================================================

class LRUCache:
    """LRU 缓存"""
    
    def __init__(self, max_size: int = 128, ttl: Optional[float] = None):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            entry = self._cache[key]
            if self._ttl and (time.time() - entry.last_accessed) > self._ttl:
                del self._cache[key]
                self._misses += 1
                return default
            self._cache.move_to_end(key)
            entry.last_accessed = time.time()
            entry.hit_count += 1
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache[key].value = value
                self._cache[key].last_accessed = time.time()
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)
                self._cache[key] = CacheEntry(key=key, value=value)
    
    def __contains__(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            if self._ttl:
                entry = self._cache[key]
                if (time.time() - entry.last_accessed) > self._ttl:
                    del self._cache[key]
                    return False
            return True
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {"size": len(self._cache), "max_size": self._max_size, "ttl": self._ttl,
                    "hits": self._hits, "misses": self._misses, "hit_rate": f"{hit_rate:.1%}"}

# ============================================================================
# TTL 缓存
# ============================================================================

class TTLCache:
    """TTL 缓存"""
    
    def __init__(self, ttl: float = 300, cleanup_interval: float = 60):
        self._cache: dict[str, CacheEntry] = {}
        self._ttl = ttl
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._cleanup_running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, args=(cleanup_interval,), daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_loop(self, interval: float) -> None:
        while self._cleanup_running:
            time.sleep(interval)
            self._cleanup_expired()
    
    def _cleanup_expired(self) -> None:
        now = time.time()
        with self._lock:
            expired = [k for k, v in self._cache.items() if (now - v.last_accessed) > self._ttl]
            for k in expired:
                self._cache.pop(k, None)
    
    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return default
            entry = self._cache[key]
            if (time.time() - entry.last_accessed) > self._ttl:
                self._cache.pop(key, None)
                self._misses += 1
                return default
            entry.last_accessed = time.time()
            entry.hit_count += 1
            self._hits += 1
            return entry.value
    
    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = CacheEntry(key=key, value=value)
    
    def __contains__(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            if (time.time() - entry.last_accessed) > self._ttl:
                self._cache.pop(key, None)
                return False
            return True
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                self._cache.pop(key)
                return True
            return False
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def stop(self) -> None:
        self._cleanup_running = False
    
    def get_stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {"size": len(self._cache), "ttl": self._ttl,
                    "hits": self._hits, "misses": self._misses, "hit_rate": f"{hit_rate:.1%}"}

# ============================================================================
# 全局实例
# ============================================================================

_file_cache: Optional[FileReadCache] = None
_cache_lock = threading.Lock()

def get_file_cache() -> FileReadCache:
    global _file_cache
    with _cache_lock:
        if _file_cache is None:
            _file_cache = FileReadCache()
        return _file_cache
