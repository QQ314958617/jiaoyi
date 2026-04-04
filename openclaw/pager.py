"""
Pager - 分页
基于 Claude Code pager.ts 设计

分页工具。
"""
from typing import Any, Callable, List, Tuple


class Pager:
    """
    分页器
    """
    
    def __init__(self, items: List = None, page_size: int = 10):
        """
        Args:
            items: 数据列表
            page_size: 每页大小
        """
        self._items = items or []
        self._page_size = page_size
    
    def page(self, page_num: int) -> List:
        """
        获取指定页
        
        Args:
            page_num: 页码（从1开始）
            
        Returns:
            页数据
        """
        if page_num < 1:
            page_num = 1
        
        start = (page_num - 1) * self._page_size
        end = start + self._page_size
        
        return self._items[start:end]
    
    def total_pages(self) -> int:
        """总页数"""
        return (len(self._items) + self._page_size - 1) // self._page_size
    
    def total_items(self) -> int:
        """总条目数"""
        return len(self._items)
    
    def has_next(self, page_num: int) -> bool:
        """是否有下一页"""
        return page_num < self.total_pages()
    
    def has_prev(self, page_num: int) -> bool:
        """是否有上一页"""
        return page_num > 1
    
    def info(self, page_num: int) -> dict:
        """
        获取分页信息
        
        Args:
            page_num: 页码
            
        Returns:
            分页信息
        """
        return {
            "page": page_num,
            "page_size": self._page_size,
            "total_pages": self.total_pages(),
            "total_items": self.total_items(),
            "has_next": self.has_next(page_num),
            "has_prev": self.has_prev(page_num),
            "items": self.page(page_num)
        }


def paginate(items: List, page: int, page_size: int) -> Tuple[List, dict]:
    """
    分页函数
    
    Args:
        items: 列表
        page: 页码
        page_size: 每页大小
        
    Returns:
        (页数据, 分页信息)
    """
    pager = Pager(items, page_size)
    return pager.page(page), pager.info(page)


def chunk_pages(items: List, page_size: int) -> List[List]:
    """
    分页（返回所有页）
    
    Args:
        items: 列表
        page_size: 每页大小
        
    Returns:
        所有页的列表
    """
    return [items[i:i+page_size] for i in range(0, len(items), page_size)]


# 导出
__all__ = [
    "Pager",
    "paginate",
    "chunk_pages",
]
