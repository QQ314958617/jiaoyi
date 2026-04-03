"""
OpenClaw Memoize + Cache
=========================
Inspired by Claude Code's src/utils/memoize.ts (300+ lines).

核心功能：
1. memoizeWithTTL — 同步函数 TTL 缓存（stale-while-refresh）
2. memoizeWithTTLAsync — 异步函数 TTL 缓存（stale-while-refresh + cold-miss dedup）
3. memoizeWithLRU — LRU 驱逐策略缓存

关键设计（Claude Code）：
- stale-while-refresh: 缓存过期后立即返回旧值，后台异步刷新
- in-flight dedup: 并发冷启动时共享同一个调用（避免 N 次重复请求）
- 内存保护: LRU 限制缓存大小

我们的落地：
- 装饰器形式
- 线程安全
- 交易数据缓存（行情/持仓/指数）
"""

from __future__ import annotations

import asyncio
import threading
import time
import json
import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TypeVar, Generic
from functools import wraps
from collections import OrderedDict

T = TypeVar("T")
F = TypeVar("F", bound=Callable)


# ============================================================================
# 缓存条目
# ============================================================================

@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""
    value: T
    timestamp: float
    refreshing: bool = False


# ============================================================================
# JSON Key 序列化
# ============================================================================

def _make_key(*args, **kwargs) -> str:
    """将函数参数序列化为字符串 key"""
    try:
        # 尝试 JSON 序列化
        key_data = {"args": args, "kwargs": kwargs}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    except (TypeError, ValueError):
        # 回退到 repr
        return hashlib.md5(
            f"{args!r}:{kwargs!r}".encode()
        ).hexdigest()[:16]


# ============================================================================
# 同步 TTL 缓存
# ============================================================================

def memoize_with_ttl(
    ttl_seconds: float = 300,
    max_size: int = 1000,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    同步函数 TTL 缓存装饰器（stale-while-refresh）。

    行为：
    1. 缓存命中且未过期 → 直接返回
    2. 缓存过期且未刷新中 → 返回旧值，后台异步刷新
    3. 缓存不存在 → 同步计算并返回

    用法：
        @memoize_with_ttl(ttl_seconds=60)
        def get_stock_price(code: str) -> float:
            return fetch_from_api(code)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: Dict[str, CacheEntry[T]] = OrderedDict()
        cache_lock = threading.Lock()

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            key = _make_key(*args, **kwargs)
            now = time.time()

            with cache_lock:
                # 缓存存在
                if key in cache:
                    entry = cache[key]

                    # 缓存过期 & 不在刷新中 → stale-while-refresh
                    if now - entry.timestamp > ttl_seconds and not entry.refreshing:
                        entry.refreshing = True

                        # 后台刷新（非阻塞）
                        def do_refresh():
                            try:
                                new_value = func(*args, **kwargs)
                                with cache_lock:
                                    if cache.get(key) is entry:
                                        cache[key] = CacheEntry(
                                            value=new_value,
                                            timestamp=time.time(),
                                            refreshing=False,
                                        )
                                    # 移到末尾（最近使用）
                                    if key in cache:
                                        cache.move_to_end(key)
                            except Exception:
                                with cache_lock:
                                    if cache.get(key) is entry:
                                        cache[key] = CacheEntry(
                                            value=entry.value,
                                            timestamp=time.time(),
                                            refreshing=False,
                                        )

                        threading.Thread(target=do_refresh, daemon=True).start()

                    # 返回缓存值（新鲜的或过期的）
                    cache.move_to_end(key)  # 更新LRU
                    return entry.value

                # 缓存不存在 → 同步计算
                try:
                    value = func(*args, **kwargs)
                    # 写入缓存
                    cache[key] = CacheEntry(value=value, timestamp=now)
                    cache.move_to_end(key)

                    # LRU 驱逐
                    while len(cache) > max_size:
                        cache.popitem(last=False)

                    return value
                except Exception:
                    raise

        # 添加 cache.clear() 方法
        wrapper.cache = lambda: (_ for _ in ([cache.clear()] if True else []))
        wrapper.cache_clear = lambda: (cache.clear() or True)
        wrapper.cache_info = lambda: {
            "size": len(cache),
            "max_size": max_size,
            "ttl": ttl_seconds,
        }

        return wrapper
    return decorator


# ============================================================================
# 异步 TTL 缓存（支持并发冷启动去重）
# ============================================================================

def memoize_with_ttl_async(
    ttl_seconds: float = 300,
    max_size: int = 1000,
) -> Callable[[Callable[..., asyncio.Awaitable[T]]], Callable[..., asyncio.Awaitable[T]]]:
    """
    异步函数 TTL 缓存装饰器（stale-while-refresh + in-flight dedup）。

    行为：
    1. 缓存命中且未过期 → 直接返回
    2. 缓存过期 & 不在刷新中 → stale-while-refresh
    3. 缓存不存在 & 有 in-flight → 等待同一请求
    4. 缓存不存在 & 无 in-flight → 发起请求

    用法：
        @memoize_with_ttl_async(ttl_seconds=60)
        async def get_stock_price(code: str) -> float:
            return await fetch_from_api(code)
    """
    def decorator(
        func: Callable[..., asyncio.Awaitable[T]]
    ) -> Callable[..., asyncio.Awaitable[T]]:
        cache: Dict[str, CacheEntry[T]] = OrderedDict()
        in_flight: Dict[str, asyncio.Task[T]] = {}  # in-flight 任务去重
        cache_lock = threading.Lock()

        async def do_refresh(key: str, entry: CacheEntry[T], args, kwargs):
            try:
                new_value = await func(*args, **kwargs)
                with cache_lock:
                    if cache.get(key) is entry:
                        cache[key] = CacheEntry(
                            value=new_value,
                            timestamp=time.time(),
                            refreshing=False,
                        )
                    if key in cache:
                        cache.move_to_end(key)
            except Exception:
                with cache_lock:
                    if cache.get(key) is entry:
                        cache[key] = CacheEntry(
                            value=entry.value,
                            timestamp=time.time(),
                            refreshing=False,
                        )
            finally:
                with cache_lock:
                    in_flight.pop(key, None)

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            key = _make_key(*args, **kwargs)
            now = time.time()

            with cache_lock:
                # 检查 in-flight（并发冷启动去重）
                if key in in_flight:
                    task = in_flight[key]
                else:
                    task = None

            # 等待 in-flight 请求完成
            if task:
                try:
                    return await task
                except Exception:
                    pass  # in-flight 失败了，继续走正常逻辑

            with cache_lock:
                # 缓存存在
                if key in cache:
                    entry = cache[key]

                    # 过期 & 不在刷新中 → stale-while-refresh
                    if now - entry.timestamp > ttl_seconds and not entry.refreshing:
                        entry.refreshing = True

                        # 创建后台刷新任务
                        async def refresh_task():
                            return await do_refresh(key, entry, args, kwargs)

                        t = asyncio.create_task(refresh_task())
                        with cache_lock:
                            in_flight[key] = t
                        t.add_done_callback(
                            lambda _: in_flight.pop(key, None)
                        )

                    cache.move_to_end(key)
                    return entry.value

                # 缓存不存在 → 发起请求
                async def new_request():
                    result = await func(*args, **kwargs)
                    with cache_lock:
                        cache[key] = CacheEntry(value=result, timestamp=time.time())
                        cache.move_to_end(key)
                        # LRU 驱逐
                        while len(cache) > max_size:
                            cache.popitem(last=False)
                        in_flight.pop(key, None)
                    return result

                t = asyncio.create_task(new_request())
                with cache_lock:
                    in_flight[key] = t

                try:
                    return await t
                except Exception:
                    with cache_lock:
                        in_flight.pop(key, None)
                    raise

        wrapper.cache = lambda: (_ for _ in ([cache.clear()] if True else []))
        wrapper.cache_clear = lambda: (
            cache.clear() or
            [t.cancel() for t in in_flight.values()] or
            in_flight.clear() or
            True
        )
        wrapper.cache_info = lambda: {
            "size": len(cache),
            "max_size": max_size,
            "ttl": ttl_seconds,
            "in_flight": len(in_flight),
        }

        return wrapper
    return decorator


# ============================================================================
# LRU 缓存（固定大小，防止内存无限增长）
# ============================================================================

def memoize_lru(
    max_size: int = 100,
    key_fn: Optional[Callable] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    LRU 缓存装饰器。

    当缓存满时，驱逐最久未使用的条目。

    用法：
        @memoize_lru(max_size=50)
        def get_stock_price(code: str) -> float:
            return fetch_from_api(code)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cache: OrderedDict[str, T] = OrderedDict()
        lock = threading.Lock()
        _key_fn = key_fn or (lambda *a, **k: _make_key(*a, **k))

        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            key = _key_fn(*args, **kwargs)

            with lock:
                if key in cache:
                    cache.move_to_end(key)  # 更新为最近使用
                    return cache[key]

                # 计算新值
                value = func(*args, **kwargs)
                cache[key] = value
                cache.move_to_end(key)

                # LRU 驱逐
                while len(cache) > max_size:
                    cache.popitem(last=False)

                return value

        wrapper.cache = lambda: (_ for _ in ([cache.clear()] if True else []))
        wrapper.cache_clear = lambda: (cache.clear() or True)
        wrapper.cache_info = lambda: {
            "size": len(cache),
            "max_size": max_size,
        }
        wrapper.cache_get = lambda key: cache.get(key)
        wrapper.cache_has = lambda key: key in cache

        return wrapper
    return decorator


# ============================================================================
# 便捷函数（直接缓存数据）
# ============================================================================

class TTLCache:
    """
    简单的 TTL 缓存类。

    用法：
        cache = TTLCache(ttl_seconds=60)
        cache.set("key", value)
        value = cache.get("key")  # None if missing or expired
    """

    def __init__(self, ttl_seconds: float = 300, max_size: int = 1000):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        """获取值，不存在或过期返回 None"""
        with self._lock:
            if key not in self._cache:
                return None
            entry = self._cache[key]
            if time.time() - entry.timestamp > self._ttl:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return entry.value

    def set(self, key: str, value: Any) -> None:
        """设置值"""
        with self._lock:
            self._cache[key] = CacheEntry(value=value, timestamp=time.time())
            self._cache.move_to_end(key)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """删除值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def __contains__(self, key: str) -> bool:
        """in 操作符"""
        return self.get(key) is not None

    def __len__(self) -> int:
        return len(self._cache)

    def info(self) -> Dict[str, Any]:
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "ttl": self._ttl,
        }
