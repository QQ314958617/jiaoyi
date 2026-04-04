"""
Table - 表格工具
基于 Claude Code table.ts 设计

表格格式化工具。
"""
from typing import Any, List


class Table:
    """
    表格
    
    创建和格式化表格。
    """
    
    def __init__(
        self,
        headers: List[str] = None,
        rows: List[List[Any]] = None,
    ):
        """
        Args:
            headers: 表头
            rows: 行数据
        """
        self.headers = headers or []
        self.rows = rows or []
        self._column_widths: List[int] = []
    
    def add_row(self, row: List[Any]) -> "Table":
        """添加行"""
        self.rows.append(row)
        return self
    
    def set_headers(self, headers: List[str]) -> "Table":
        """设置表头"""
        self.headers = headers
        return self
    
    def _calculate_widths(self) -> None:
        """计算列宽"""
        self._column_widths = []
        
        num_cols = len(self.headers) if self.headers else (len(self.rows[0]) if self.rows else 0)
        
        # 初始化为表头宽度
        for i in range(num_cols):
            header = self.headers[i] if self.headers and i < len(self.headers) else ''
            self._column_widths.append(len(str(header)))
        
        # 检查数据宽度
        for row in self.rows:
            for i, cell in enumerate(row):
                if i < len(self._column_widths):
                    self._column_widths[i] = max(self._column_widths[i], len(str(cell)))
    
    def to_string(self, padding: int = 2) -> str:
        """转换为字符串"""
        self._calculate_widths()
        
        lines = []
        
        # 表头
        if self.headers:
            header_cells = []
            for i, header in enumerate(self.headers):
                width = self._column_widths[i]
                header_cells.append(str(header).ljust(width))
            lines.append(' ' * padding + (' ' * padding).join(header_cells))
            
            # 分隔线
            separator_cells = []
            for width in self._column_widths:
                separator_cells.append('-' * width)
            lines.append(' ' * padding + (' ' * padding).join(separator_cells))
        
        # 数据行
        for row in self.rows:
            row_cells = []
            for i, cell in enumerate(row):
                if i < len(self._column_widths):
                    row_cells.append(str(cell).ljust(self._column_widths[i]))
            lines.append(' ' * padding + (' ' * padding).join(row_cells))
        
        return '\n'.join(lines)
    
    def __str__(self) -> str:
        return self.to_string()
    
    def print(self) -> None:
        """打印表格"""
        print(self.to_string())


def create_table(headers: List[str] = None) -> Table:
    """
    创建表格
    
    Args:
        headers: 表头
        
    Returns:
        Table实例
    """
    return Table(headers=headers)


def print_table(data: List[dict], headers: List[str] = None) -> None:
    """
    打印数据表格
    
    Args:
        data: 数据字典列表
        headers: 指定表头
    """
    if not data:
        return
    
    # 自动获取headers
    if headers is None:
        headers = list(data[0].keys())
    
    # 创建表格
    table = Table(headers=headers)
    
    # 添加行
    for row in data:
        table.add_row([row.get(h, '') for h in headers])
    
    table.print()


# 导出
__all__ = [
    "Table",
    "create_table",
    "print_table",
]
