"""
OpenClaw Context Cache System
==============================
Inspired by Claude Code's context.ts memoize pattern.

Claude Code 的设计：
- getGitStatus() 用 memoize 缓存，对话期间只查一次
- getSystemContext() 缓存 git/status/claude.md
- setSystemPromptInjection() 会清除缓存

我们实现：
- Session 级别的上下文缓存
- 定时失效机制
- 心跳期间统一刷新
"""

import time
import functools
import threading
from typing import Any, Callable, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass, field

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """单条缓存条目"""
    value: T
    created_at: float
    expires_at: Optional[float] = None  # None = 永不过期
    tag: Optional[str] = None           # 用于按标签批量失效

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class ContextCache:
    """
    线程安全的上下文缓存。

    用法:
        cache = ContextCache()

        # 存
        cache.set("portfolio", portfolio_data, ttl=300)  # 5分钟过期

        # 取
        data = cache.get("portfolio")
        if data is None:
            data = fetch_portfolio()
            cache.set("portfolio", data)

        # 清除
        cache.invalidate("portfolio")
        cache.clear()  # 全部清除
        cache.invalidate_by_tag("daily_review")  # 按标签批量清除
    """

    def __init__(self, default_ttl: Optional[float] = None):
        """
        Args:
            default_ttl: 默认过期秒数，None=永不过期
        """
        self._store: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        tag: Optional[str] = None,
    ) -> None:
        """存入缓存"""
        with self._lock:
            expires_at = None
            if ttl is not None or self._default_ttl is not None:
                lifetime = ttl if ttl is not None else self._default_ttl
                expires_at = time.time() + lifetime

            self._store[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
                tag=tag,
            )

    def get(self, key: str, allow_expired: bool = False) -> Any:
        """
        获取缓存。

        Args:
            key: 缓存键
            allow_expired: True=即使过期也返回（用于容错）

        Returns:
            缓存值，不存在或已过期返回 None
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired() and not allow_expired:
                self._misses += 1
                del self._store[key]
                return None

            self._hits += 1
            return entry.value

    def get_or_compute(self, key: str, compute_fn: Callable[[], Any], ttl: Optional[float] = None) -> Any:
        """
        缓存取值或计算。
        如果缓存不存在，调用 compute_fn() 计算并缓存。
        线程安全。
        """
        with self._lock:
            existing = self.get(key)
            if existing is not None:
                return existing

            value = compute_fn()
            self.set(key, value, ttl=ttl)
            return value

    def invalidate(self, key: str) -> bool:
        """删除指定缓存，返回是否实际删除了什么"""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def invalidate_by_tag(self, tag: str) -> int:
        """按标签批量删除，返回删除数量"""
        with self._lock:
            to_delete = [
                k for k, v in self._store.items()
                if v.tag == tag
            ]
            for k in to_delete:
                del self._store[k]
            return len(to_delete)

    def clear(self) -> int:
        """清空所有缓存，返回删除数量"""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count

    def stats(self) -> Dict[str, Any]:
        """缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "total": total,
                "hit_rate": round(hit_rate, 3),
                "size": len(self._store),
                "keys": list(self._store.keys()),
            }

    def cleanup_expired(self) -> int:
        """清理所有过期条目，返回清理数量"""
        with self._lock:
            expired_keys = [
                k for k, v in self._store.items()
                if v.is_expired()
            ]
            for k in expired_keys:
                del self._store[k]
            return len(expired_keys)


# ============================================================================
# 全局缓存实例（对话级别）
# ============================================================================

# 对话级缓存（整个会话期间有效）
_session_cache = ContextCache()

# 每日缓存（每天北京时间0点自动失效）
_daily_cache = ContextCache()

# 心跳缓存（每次心跳前自动刷新）
_heartbeat_cache = ContextCache(default_ttl=30)  # 30秒过期


def session_cache() -> ContextCache:
    """获取会话级缓存"""
    return _session_cache


def daily_cache() -> ContextCache:
    """获取每日级缓存"""
    return _daily_cache


def heartbeat_cache() -> ContextCache:
    """获取心跳缓存（短期，自动过期）"""
    return _heartbeat_cache


# ============================================================================
# 装饰器（简化缓存使用）
# ============================================================================

def cached(
    ttl: Optional[float] = None,
    cache: Optional[ContextCache] = None,
    key_fn: Optional[Callable[..., str]] = None,
):
    """
    缓存装饰器。

    用法:
        @cached(ttl=60, cache=session_cache())
        def get_portfolio():
            ...

        # 自定义缓存键
        @cached(key_fn=lambda code, **kw: f"quote_{code}")
        def get_quote(code: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _cache = cache or _session_cache
            cache_key = key_fn(*args, **kwargs) if key_fn else func.__name__

            result = _cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl=ttl)
            return result

        # 附带给函数添加缓存管理方法
        wrapper.cache_invalidate = lambda: _cache.invalidate(cache_key or func.__name__)
        wrapper.cache_key = cache_key if cache_key else func.__name__
        return wrapper
    return decorator


# ============================================================================
# 缓存失效集成点
# ============================================================================

def invalidate_all_caches() -> None:
    """清除所有缓存（用于系统重置/配置变更）"""
    session_cache().clear()
    daily_cache().clear()
    heartbeat_cache().clear()


def on_config_changed() -> None:
    """
    配置变更时的缓存清理钩子。
    任何配置写入后调用此函数。
    """
    # 配置变更通常影响所有层，保守策略是全清
    session_cache().invalidate_by_tag("config")
    invalidate_all_caches()
