"""
Batch2 - 批处理
基于 Claude Code batch.ts 设计

批处理工具。
"""
import time
import threading
from typing import Callable, List, Any


class Batcher:
    """
    批处理器
    
    累积一定数量或时间后批量执行。
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        batch_interval: float = 1.0,
        processor: Callable[[List], Any] = None
    ):
        """
        Args:
            batch_size: 批大小
            batch_interval: 批处理间隔（秒）
            processor: 批处理函数
        """
        self._batch_size = batch_size
        self._batch_interval = batch_interval
        self._processor = processor or (lambda items: items)
        self._buffer: List = []
        self._timer: threading.Timer = None
        self._lock = threading.Lock()
    
    def add(self, item: Any) -> None:
        """添加项目"""
        with self._lock:
            self._buffer.append(item)
            
            if len(self._buffer) >= self._batch_size:
                self._flush()
            elif not self._timer:
                self._timer = threading.Timer(self._batch_interval, self._on_timer)
                self._timer.start()
    
    def _on_timer(self) -> None:
        """定时触发"""
        with self._lock:
            if self._buffer:
                self._flush()
    
    def _flush(self) -> None:
        """清空缓冲区"""
        if self._timer:
            self._timer.cancel()
            self._timer = None
        
        if self._buffer:
            items = list(self._buffer)
            self._buffer.clear()
            
            try:
                self._processor(items)
            except Exception:
                pass
    
    def flush(self) -> None:
        """手动清空"""
        with self._lock:
            self._flush()
    
    @property
    def size(self) -> int:
        """当前缓冲大小"""
        return len(self._buffer)


def batch(items: List, size: int) -> List[List]:
    """
    将列表分批
    
    Args:
        items: 列表
        size: 批大小
        
    Returns:
        批次列表
    """
    return [items[i:i + size] for i in range(0, len(items), size)]


def batch_by(items: List, key_fn: Callable) -> dict:
    """
    按键分批
    
    Args:
        items: 列表
        key_fn: 键函数
        
    Returns:
        { key: [items] }
    """
    result = {}
    for item in items:
        key = key_fn(item)
        if key not in result:
            result[key] = []
        result[key].append(item)
    return result


def chunk(items: List, size: int) -> List[List]:
    """分块（别名）"""
    return batch(items, size)


# 导出
__all__ = [
    "Batcher",
    "batch",
    "batch_by",
    "chunk",
]
