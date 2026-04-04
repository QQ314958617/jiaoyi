"""
Buffered Writer - 缓冲写入器
基于 Claude Code bufferedWriter.ts 设计

提供缓冲写入功能，减少IO操作。
"""
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class BufferedWriter:
    """缓冲写入器接口"""
    write: Callable[[str], None]
    flush: Callable[[], None]
    dispose: Callable[[], None]


class BufferedWriterImpl:
    """
    缓冲写入器实现
    
    将多次小写入合并为批量写入，减少IO操作。
    支持定时刷新和手动刷新。
    """
    
    def __init__(
        self,
        write_fn: Callable[[str], None],
        flush_interval_ms: int = 1000,
        max_buffer_size: int = 100,
        max_buffer_bytes: int = 1024 * 1024,  # 1MB
        immediate_mode: bool = False,
    ):
        """
        Args:
            write_fn: 实际写入函数
            flush_interval_ms: 刷新间隔（毫秒）
            max_buffer_size: 最大缓冲条目数
            max_buffer_bytes: 最大缓冲字节数
            immediate_mode: 是否立即写入模式
        """
        self._write_fn = write_fn
        self._flush_interval_ms = flush_interval_ms
        self._max_buffer_size = max_buffer_size
        self._max_buffer_bytes = max_buffer_bytes
        self._immediate_mode = immediate_mode
        
        self._buffer: list[str] = []
        self._buffer_bytes = 0
        self._flush_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
    
    def write(self, content: str) -> None:
        """
        写入内容到缓冲区
        
        Args:
            content: 要写入的内容
        """
        if self._immediate_mode:
            self._write_fn(content)
            return
        
        with self._lock:
            self._buffer.append(content)
            self._buffer_bytes += len(content.encode())
            
            # 安排定时刷新
            if not self._flush_timer:
                self._schedule_flush()
            
            # 检查是否需要立即刷新
            if len(self._buffer) >= self._max_buffer_size or \
               self._buffer_bytes >= self._max_buffer_bytes:
                self._flush_deferred()
    
    def flush(self) -> None:
        """立即刷新缓冲区"""
        with self._lock:
            self._do_flush_unlocked()
    
    def dispose(self) -> None:
        """释放资源"""
        self.flush()
    
    def _schedule_flush(self) -> None:
        """安排定时刷新"""
        if self._flush_timer:
            self._flush_timer.cancel()
        
        self._flush_timer = threading.Timer(
            self._flush_interval_ms / 1000,
            self._flush,
        )
        self._flush_timer.daemon = True
        self._flush_timer.start()
    
    def _cancel_timer(self) -> None:
        """取消定时器"""
        if self._flush_timer:
            self._flush_timer.cancel()
            self._flush_timer = None
    
    def _do_flush_unlocked(self) -> None:
        """执行刷新（假设已持有锁）"""
        if not self._buffer:
            return
        
        content = ''.join(self._buffer)
        self._buffer.clear()
        self._buffer_bytes = 0
        self._cancel_timer()
        
        self._write_fn(content)
    
    def _flush(self) -> None:
        """刷新（在线程中调用）"""
        with self._lock:
            self._do_flush_unlocked()
    
    def _flush_deferred(self) -> None:
        """延迟刷新（在下一个事件循环中）"""
        with self._lock:
            if not self._buffer:
                return
            
            # 交换缓冲区
            buffer = self._buffer
            self._buffer = []
            self._buffer_bytes = 0
            self._cancel_timer()
        
        # 在新线程中执行实际写入
        def do_write():
            content = ''.join(buffer)
            self._write_fn(content)
        
        thread = threading.Thread(target=do_write)
        thread.daemon = True
        thread.start()
    
    def __enter__(self) -> "BufferedWriterImpl":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.dispose()


def create_buffered_writer(
    write_fn: Callable[[str], None],
    flush_interval_ms: int = 1000,
    max_buffer_size: int = 100,
    max_buffer_bytes: int = 1024 * 1024,
    immediate_mode: bool = False,
) -> BufferedWriter:
    """
    创建缓冲写入器
    
    Args:
        write_fn: 实际写入函数
        flush_interval_ms: 刷新间隔
        max_buffer_size: 最大缓冲条目数
        max_buffer_bytes: 最大缓冲字节数
        immediate_mode: 立即写入模式
        
    Returns:
        BufferedWriter对象
    """
    writer = BufferedWriterImpl(
        write_fn=write_fn,
        flush_interval_ms=flush_interval_ms,
        max_buffer_size=max_buffer_size,
        max_buffer_bytes=max_buffer_bytes,
        immediate_mode=immediate_mode,
    )
    
    return BufferedWriter(
        write=writer.write,
        flush=writer.flush,
        dispose=writer.dispose,
    )


# 导出
__all__ = [
    "BufferedWriter",
    "BufferedWriterImpl",
    "create_buffered_writer",
]
