"""
Batch - 批处理
基于 Claude Code batch.ts 设计

批处理工具。
"""
import asyncio
from typing import Any, Callable, List


def batch(items: List[Any], size: int) -> List[List[Any]]:
    """
    分批
    
    Args:
        items: 项目列表
        size: 批大小
        
    Returns:
        批次列表
    """
    return [items[i:i + size] for i in range(0, len(items), size)]


def chunk(items: List[Any], size: int) -> List[List[Any]]:
    """chunk的别名"""
    return batch(items, size)


async def batch_async(
    items: List[Any],
    size: int,
    processor: Callable,
) -> List[Any]:
    """
    异步批处理
    
    Args:
        items: 项目列表
        size: 批大小
        processor: 处理函数
        
    Returns:
        处理结果列表
    """
    results = []
    
    for batch_items in batch(items, size):
        batch_results = []
        
        for item in batch_items:
            if asyncio.iscoroutinefunction(processor):
                result = await processor(item)
            else:
                result = processor(item)
            batch_results.append(result)
        
        results.extend(batch_results)
    
    return results


async def batch_async_parallel(
    items: List[Any],
    size: int,
    processor: Callable,
    max_concurrency: int = 5,
) -> List[Any]:
    """
    并行异步批处理
    
    Args:
        items: 项目列表
        size: 批大小
        processor: 处理函数
        max_concurrency: 最大并发数
        
    Returns:
        处理结果列表
    """
    batches = batch(items, size)
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_batch(batch_items: List[Any]) -> List[Any]:
        async with semaphore:
            results = []
            for item in batch_items:
                if asyncio.iscoroutinefunction(processor):
                    result = await processor(item)
                else:
                    result = processor(item)
                results.append(result)
            return results
    
    batch_results = await asyncio.gather(*[process_batch(b) for b in batches])
    
    # 展平结果
    return [item for batch in batch_results for item in batch]


def process_batch(
    items: List[Any],
    size: int,
    processor: Callable,
) -> List[Any]:
    """
    同步批处理
    
    Args:
        items: 项目列表
        size: 批大小
        processor: 处理函数
        
    Returns:
        处理结果列表
    """
    results = []
    
    for batch_items in batch(items, size):
        for item in batch_items:
            result = processor(item)
            results.append(result)
    
    return results


class BatchProcessor:
    """
    批处理器
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        processor: Callable = None,
    ):
        """
        Args:
            batch_size: 批大小
            processor: 处理函数
        """
        self.batch_size = batch_size
        self.processor = processor
    
    def process(self, items: List[Any]) -> List[Any]:
        """处理"""
        return process_batch(items, self.batch_size, self.processor)
    
    async def process_async(self, items: List[Any]) -> List[Any]:
        """异步处理"""
        return await batch_async(items, self.batch_size, self.processor)


# 导出
__all__ = [
    "batch",
    "chunk",
    "batch_async",
    "batch_async_parallel",
    "process_batch",
    "BatchProcessor",
]
