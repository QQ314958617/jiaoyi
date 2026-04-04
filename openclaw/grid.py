"""
Grid - 网格
基于 Claude Code grid.ts 设计

网格工具。
"""
from typing import Any, Callable, List, Tuple


class Grid:
    """
    二维网格
    """
    
    def __init__(self, rows: int, cols: int, default: Any = None):
        """
        Args:
            rows: 行数
            cols: 列数
            default: 默认值
        """
        self._rows = rows
        self._cols = cols
        self._default = default
        self._data = [[default for _ in range(cols)] for _ in range(rows)]
    
    def get(self, row: int, col: int, default: Any = None) -> Any:
        """
        获取单元格
        
        Args:
            row: 行索引
            col: 列索引
            
        Returns:
            单元格值
        """
        if 0 <= row < self._rows and 0 <= col < self._cols:
            return self._data[row][col]
        return default if default is not None else self._default
    
    def set(self, row: int, col: int, value: Any) -> bool:
        """
        设置单元格
        
        Args:
            row: 行索引
            col: 列索引
            value: 值
            
        Returns:
            是否成功
        """
        if 0 <= row < self._rows and 0 <= col < self._cols:
            self._data[row][col] = value
            return True
        return False
    
    def in_bounds(self, row: int, col: int) -> bool:
        """是否在边界内"""
        return 0 <= row < self._rows and 0 <= col < self._cols
    
    def neighbors(self, row: int, col: int, diagonal: bool = False) -> List[Tuple[int, int]]:
        """
        获取邻居
        
        Args:
            row: 行索引
            col: 列索引
            diagonal: 是否包含对角
            
        Returns:
            邻居坐标列表
        """
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1)  # 上下左右
        ]
        if diagonal:
            directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        
        result = []
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if self.in_bounds(nr, nc):
                result.append((nr, nc))
        
        return result
    
    def fill(self, value: Any) -> None:
        """填充网格"""
        self._data = [[value for _ in range(self._cols)] for _ in range(self._rows)]
    
    def map(self, fn: Callable) -> "Grid":
        """
        映射网格
        
        Args:
            fn: (value, row, col) -> new_value
            
        Returns:
            新网格
        """
        new_grid = Grid(self._rows, self._cols, self._default)
        for r in range(self._rows):
            for c in range(self._cols):
                new_grid.set(r, c, fn(self._data[r][c], r, c))
        return new_grid
    
    @property
    def rows(self) -> int:
        return self._rows
    
    @property
    def cols(self) -> int:
        return self._cols
    
    def to_list(self) -> List[List]:
        """转为列表"""
        return [row[:] for row in self._data]
    
    def __str__(self) -> str:
        return '\n'.join(' '.join(str(cell) for cell in row) for row in self._data)


# 导出
__all__ = [
    "Grid",
]
