"""
Lazy - 惰性求值
基于 Claude Code lazy.ts 设计

惰性求值工具。
"""
from typing import Any, Callable, Generator, Optional


class Lazy:
    """
    惰性列表
    
    延迟计算，只在需要时求值。
    """
    
    def __init__(self, source: Generator = None):
        """
        Args:
            source: 生成器函数
        """
        self._source = source
        self._cache: list = []
        self._exhausted = False
        self._generator = None
    
    def _ensure_generator(self) -> Generator:
        """确保生成器已创建"""
        if self._generator is None and self._source:
            self._generator = self._source()
        return self._generator
    
    def _fetch_next(self) -> Optional[Any]:
        """获取下一个元素"""
        try:
            gen = self._ensure_generator()
            if gen is None:
                return None
            return next(gen)
        except StopIteration:
            self._exhausted = True
            return None
    
    def head(self) -> Optional[Any]:
        """获取第一个元素"""
        if not self._cache:
            item = self._fetch_next()
            if item is not None:
                self._cache.append(item)
        return self._cache[0] if self._cache else None
    
    def tail(self) -> "Lazy":
        """获取除第一个外的惰性列表"""
        if not self._cache:
            self.head()
        
        def generator():
            gen = self._ensure_generator()
            while True:
                try:
                    yield next(gen)
                except StopIteration:
                    return
        
        new_lazy = Lazy(generator)
        new_lazy._cache = []  # 清空缓存
        return new_lazy
    
    def take(self, n: int) -> list:
        """取前n个"""
        result = []
        while len(result) < n:
            if len(self._cache) > len(result):
                result.append(self._cache[len(result)])
            else:
                item = self._fetch_next()
                if item is None:
                    break
                self._cache.append(item)
                result.append(item)
        return result
    
    def skip(self, n: int) -> list:
        """跳过前n个"""
        while len(self._cache) < n:
            item = self._fetch_next()
            if item is None:
                break
            self._cache.append(item)
        
        # 跳过缓存中的元素
        skipped = self._cache[:n]
        self._cache = self._cache[n:]
        return skipped
    
    def map(self, fn: Callable) -> "Lazy":
        """映射"""
        def generator():
            gen = self._ensure_generator()
            if gen:
                for item in gen:
                    yield fn(item)
        
        new_lazy = Lazy(generator)
        # 需要时转换缓存
        new_lazy._cache = [fn(x) for x in self._cache]
        return new_lazy
    
    def filter(self, predicate: Callable) -> "Lazy":
        """过滤"""
        def generator():
            gen = self._ensure_generator()
            if gen:
                for item in gen:
                    if predicate(item):
                        yield item
        
        new_lazy = Lazy(generator)
        new_lazy._cache = [x for x in self._cache if predicate(x)]
        return new_lazy
    
    def reduce(self, fn: Callable, initial: Any = None) -> Any:
        """归约"""
        result = initial
        
        for item in self:
            if result is None:
                result = item
            else:
                result = fn(result, item)
        
        return result
    
    def for_each(self, fn: Callable) -> None:
        """遍历（消费所有元素）"""
        for item in self:
            fn(item)
    
    def collect(self) -> list:
        """收集所有元素"""
        result = list(self._cache)
        gen = self._ensure_generator()
        if gen:
            for item in gen:
                result.append(item)
                self._cache.append(item)
        self._exhausted = True
        return result
    
    def is_empty(self) -> bool:
        """是否为空"""
        return self.head() is None
    
    def __iter__(self):
        """迭代"""
        # 先返回缓存
        for item in self._cache:
            yield item
        
        # 再返回剩余元素
        gen = self._ensure_generator()
        if gen:
            while not self._exhausted:
                try:
                    item = next(gen)
                    self._cache.append(item)
                    yield item
                except StopIteration:
                    self._exhausted = True


def lazy_range(start: int, end: int = None, step: int = 1) -> Lazy:
    """
    惰性数值范围
    
    Args:
        start: 起始
        end: 结束
        step: 步长
    """
    if end is None:
        end = start
        start = 0
    
    def generator():
        current = start
        while current < end:
            yield current
            current += step
    
    return Lazy(generator)


def lazy_map(fn: Callable, *sources) -> Lazy:
    """惰性映射多个序列"""
    def generator():
        for items in zip(*sources):
            yield fn(*items)
    
    return Lazy(generator)


# 导出
__all__ = [
    "Lazy",
    "lazy_range",
    "lazy_map",
]
