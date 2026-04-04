"""
AsyncIter - 异步迭代器
基于 Claude Code asyncIter.ts 设计

异步迭代工具。
"""
import asyncio
from typing import Any, AsyncIterator, Callable, List


async def async_map(
    items: List[Any],
    fn: Callable,
    concurrency: int = None,
) -> List[Any]:
    """
    异步映射
    
    Args:
        items: 列表
        fn: 异步函数
        concurrency: 最大并发数
        
    Returns:
        结果列表
    """
    if concurrency:
        semaphore = asyncio.Semaphore(concurrency)
        
        async def limited_fn(item):
            async with semaphore:
                return await fn(item)
        
        return await asyncio.gather(*[limited_fn(item) for item in items])
    
    return await asyncio.gather(*[fn(item) for item in items])


async def async_filter(
    items: List[Any],
    fn: Callable,
) -> List[Any]:
    """
    异步过滤
    
    Args:
        items: 列表
        fn: 异步判断函数
        
    Returns:
        过滤后的列表
    """
    results = await asyncio.gather(*[fn(item) for item in items])
    return [item for item, keep in zip(items, results) if keep]


async def async_reduce(
    items: List[Any],
    fn: Callable,
    initial: Any = None,
) -> Any:
    """
    异步归约
    
    Args:
        items: 列表
        fn: 异步归约函数
        initial: 初始值
        
    Returns:
        归约结果
    """
    result = initial
    
    for item in items:
        result = await fn(result, item)
    
    return result


async def async_flatten(
    async_items: AsyncIterator,
) -> List[Any]:
    """
    异步扁平化
    
    Args:
        async_items: 异步迭代器
        
    Returns:
        扁平化后的列表
    """
    results = []
    
    async for item in async_items:
        if isinstance(item, (list, tuple)):
            results.extend(item)
        else:
            results.append(item)
    
    return results


async def async_first(async_iter: AsyncIterator) -> Any:
    """获取第一个元素"""
    async for item in async_iter:
        return item
    return None


async def async_collect(async_iter: AsyncIterator) -> List[Any]:
    """收集所有元素"""
    return [item async for item in async_iter]


async def async_batch(
    async_iter: AsyncIterator,
    size: int,
) -> AsyncIterator[List[Any]]:
    """
    异步批迭代
    
    Args:
        async_iter: 异步迭代器
        size: 批大小
        
    Yields:
        批次
    """
    batch = []
    
    async for item in async_iter:
        batch.append(item)
        
        if len(batch) >= size:
            yield batch
            batch = []
    
    if batch:
        yield batch


async def async_take(
    async_iter: AsyncIterator,
    n: int,
) -> List[Any]:
    """
    获取前n个
    
    Args:
        async_iter: 异步迭代器
        n: 数量
        
    Returns:
        前n个元素
    """
    results = []
    
    async for item in async_iter:
        results.append(item)
        if len(results) >= n:
            break
    
    return results


async def async_each(
    items: List[Any],
    fn: Callable,
) -> None:
    """
    异步遍历
    
    Args:
        items: 列表
        fn: 异步函数
    """
    await asyncio.gather(*[fn(item) for item in items])


# 导出
__all__ = [
    "async_map",
    "async_filter",
    "async_reduce",
    "async_flatten",
    "async_first",
    "async_collect",
    "async_batch",
    "async_take",
    "async_each",
]
