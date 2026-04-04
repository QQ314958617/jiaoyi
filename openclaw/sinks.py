"""
Sinks - 日志输出
基于 Claude Code sinks.ts 设计

日志输出工具。
"""
import sys
import os
from typing import Optional, Callable


class ConsoleSink:
    """控制台输出"""
    
    def __init__(self, prefix: str = ""):
        self._prefix = prefix
    
    def write(self, message: str):
        """写入"""
        print(f"{self._prefix}{message}")


class FileSink:
    """文件输出"""
    
    def __init__(self, path: str, append: bool = True):
        self._path = path
        self._mode = "a" if append else "w"
    
    def write(self, message: str):
        """写入"""
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, self._mode) as f:
            f.write(message + "\n")
        self._mode = "a"


class BufferedSink:
    """缓冲输出"""
    
    def __init__(self, sink, buffer_size: int = 100):
        self._sink = sink
        self._buffer = []
        self._buffer_size = buffer_size
    
    def write(self, message: str):
        """写入缓冲区"""
        self._buffer.append(message)
        if len(self._buffer) >= self._buffer_size:
            self.flush()
    
    def flush(self):
        """刷新"""
        for msg in self._buffer:
            self._sink.write(msg)
        self._buffer = []


class FilteredSink:
    """过滤输出"""
    
    def __init__(self, sink, filter_fn: Callable[[str], bool]):
        self._sink = sink
        self._filter = filter_fn
    
    def write(self, message: str):
        """条件写入"""
        if self._filter(message):
            self._sink.write(message)


class MultiSink:
    """多重输出"""
    
    def __init__(self, *sinks):
        self._sinks = list(sinks)
    
    def add(self, sink):
        """添加sink"""
        self._sinks.append(sink)
    
    def write(self, message: str):
        """写入所有"""
        for sink in self._sinks:
            sink.write(message)


# 全局sink
_default_sink = ConsoleSink()


def set_sink(sink):
    """设置全局sink"""
    global _default_sink
    _default_sink = sink


def write(message: str):
    """写入"""
    _default_sink.write(message)


def to_file(path: str, append: bool = True) -> FileSink:
    """创建文件sink"""
    return FileSink(path, append)


def to_buffered(sink, buffer_size: int = 100) -> BufferedSink:
    """创建缓冲sink"""
    return BufferedSink(sink, buffer_size)


def to_filtered(sink, filter_fn: Callable) -> FilteredSink:
    """创建过滤sink"""
    return FilteredSink(sink, filter_fn)


def to_multi(*sinks) -> MultiSink:
    """创建多重sink"""
    return MultiSink(*sinks)


# 导出
__all__ = [
    "ConsoleSink",
    "FileSink",
    "BufferedSink",
    "FilteredSink",
    "MultiSink",
    "set_sink",
    "write",
    "to_file",
    "to_buffered",
    "to_filtered",
    "to_multi",
]
