"""
Stream - 流
基于 Claude Code stream.ts 设计

流处理工具。
"""
from typing import Any, Callable, Generator, Iterable, Iterator, List


class Stream:
    """
    流
    
    函数式数据处理。
    """
    
    def __init__(self, source: Iterable):
        """
        Args:
            source: 数据源
        """
        self._source = source
        self._operations: List[Callable] = []
    
    def map(self, fn: Callable) -> "Stream":
        """映射"""
        def operation(iterable):
            for item in iterable:
                yield fn(item)
        
        new_stream = Stream(self._source)
        new_stream._operations = self._operations + [operation]
        return new_stream
    
    def filter(self, predicate: Callable) -> "Stream":
        """过滤"""
        def operation(iterable):
            for item in iterable:
                if predicate(item):
                    yield item
        
        new_stream = Stream(self._source)
        new_stream._operations = self._operations + [operation]
        return new_stream
    
    def flat_map(self, fn: Callable) -> "Stream":
        """扁平映射"""
        def operation(iterable):
            for item in iterable:
                for result in fn(item):
                    yield result
        
        new_stream = Stream(self._source)
        new_stream._operations = self._operations + [operation]
        return new_stream
    
    def take(self, n: int) -> "Stream":
        """取前n个"""
        def operation(iterable):
            for i, item in enumerate(iterable):
                if i < n:
                    yield item
                else:
                    break
        
        new_stream = Stream(self._source)
        new_stream._operations = self._operations + [operation]
        return new_stream
    
    def skip(self, n: int) -> "Stream":
        """跳过前n个"""
        def operation(iterable):
            for i, item in enumerate(iterable):
                if i >= n:
                    yield item
        
        new_stream = Stream(self._source)
        new_stream._operations = self._operations + [operation]
        return new_stream
    
    def limit(self, n: int) -> "Stream":
        """限制数量（take别名）"""
        return self.take(n)
    
    def distinct(self) -> "Stream":
        """去重"""
        seen = set()
        
        def operation(iterable):
            for item in iterable:
                if item not in seen:
                    seen.add(item)
                    yield item
        
        new_stream = Stream(self._source)
        new_stream._operations = self._operations + [operation]
        return new_stream
    
    def sorted(self, key: Callable = None, reverse: bool = False) -> "Stream":
        """排序"""
        def operation(iterable):
            return sorted(iterable, key=key, reverse=reverse)
        
        new_stream = Stream(self._source)
        new_stream._operations = self._operations + [operation]
        return new_stream
    
    def reduce(self, fn: Callable, initial: Any = None) -> Any:
        """归约"""
        result = initial
        for item in self:
            if result is None:
                result = item
            else:
                result = fn(result, item)
        return result
    
    def collect(self) -> List:
        """收集为列表"""
        return list(self)
    
    def count(self) -> int:
        """计数"""
        return sum(1 for _ in self)
    
    def first(self) -> Any:
        """第一个"""
        for item in self:
            return item
        return None
    
    def last(self) -> Any:
        """最后一个"""
        last = None
        for item in self:
            last = item
        return last
    
    def for_each(self, fn: Callable) -> None:
        """遍历"""
        for item in self:
            fn(item)
    
    def any_match(self, predicate: Callable) -> bool:
        """是否有任意匹配"""
        for item in self:
            if predicate(item):
                return True
        return False
    
    def all_match(self, predicate: Callable) -> bool:
        """是否全部匹配"""
        for item in self:
            if not predicate(item):
                return False
        return True
    
    def none_match(self, predicate: Callable) -> bool:
        """是否都不匹配"""
        return not self.any_match(predicate)
    
    def __iter__(self) -> Iterator:
        """迭代"""
        iterable = self._source
        for op in self._operations:
            iterable = op(iterable)
        return iter(iterable)


def of(*items) -> Stream:
    """从数据创建流"""
    return Stream(items)


def from_iterable(iterable: Iterable) -> Stream:
    """从可迭代对象创建流"""
    return Stream(iterable)


def range(start: int, end: int, step: int = 1) -> Stream:
    """数值范围流"""
    def generate():
        current = start
        while current < end:
            yield current
            current += step
    return Stream(generate())


# 导出
__all__ = [
    "Stream",
    "of",
    "from_iterable",
    "range",
]
