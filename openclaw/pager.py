"""
Pager - 分页
基于 Claude Code pager.ts 设计

分页工具。
"""
from typing import List, Any, Callable


class Pager:
    """
    分页器
    """
    
    def __init__(self, items: List[Any], page_size: int = 10):
        """
        Args:
            items: 列表
            page_size: 每页大小
        """
        self._items = items
        self._page_size = page_size
        self._current = 0
    
    @property
    def total(self) -> int:
        """总页数"""
        return (len(self._items) + self._page_size - 1) // self._page_size
    
    @property
    def current(self) -> int:
        """当前页(1-based)"""
        return self._current + 1
    
    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self._current > 0
    
    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self._current < self.total - 1
    
    def page(self, index: int = 0) -> List[Any]:
        """获取指定页"""
        index = max(0, min(index, self.total - 1))
        start = index * self._page_size
        return self._items[start:start + self._page_size]
    
    def first(self) -> List[Any]:
        """第一页"""
        return self.page(0)
    
    def last(self) -> List[Any]:
        """最后一页"""
        return self.page(self.total - 1)
    
    def next(self) -> List[Any]:
        """下一页"""
        if self.has_next:
            self._current += 1
        return self.page(self._current)
    
    def prev(self) -> List[Any]:
        """上一页"""
        if self.has_prev:
            self._current -= 1
        return self.page(self._current)
    
    def go(self, index: int) -> List[Any]:
        """跳转到指定页"""
        self._current = max(0, min(index, self.total - 1))
        return self.page(self._current)


def paginate(items: List[Any], page: int = 1, page_size: int = 10) -> dict:
    """
    分页
    
    Returns:
        {
            "items": [...],
            "page": 1,
            "page_size": 10,
            "total": 100,
            "total_pages": 10,
            "has_next": True,
            "has_prev": False
        }
    """
    total = len(items)
    total_pages = (total + page_size - 1) // page_size
    
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


# 导出
__all__ = [
    "Pager",
    "paginate",
]
