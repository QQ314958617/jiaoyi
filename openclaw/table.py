"""
Table - 表格
基于 Claude Code table.ts 设计

表格工具。
"""
from typing import Any, Callable, List


def ascii_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    ASCII表格
    
    Args:
        headers: 表头
        rows: 行数据
        
    Returns:
        ASCII表格字符串
    """
    # 计算每列宽度
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 分隔线
    sep = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'
    
    # 表头
    header_line = '|' + '|'.join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + '|'
    
    # 数据行
    data_lines = []
    for row in rows:
        line = '|' + '|'.join(f" {str(cell):<{col_widths[i]}} " for i, cell in enumerate(row)) + '|'
        data_lines.append(line)
    
    return '\n'.join([sep, header_line, sep] + data_lines + [sep])


def markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    Markdown表格
    
    Args:
        headers: 表头
        rows: 行数据
        
    Returns:
        Markdown表格字符串
    """
    # 计算每列宽度
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 表头
    header_line = '|' + '|'.join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + '|'
    
    # 分隔线
    sep = '|' + '|'.join('-' * (w + 2) for w in col_widths) + '|'
    
    # 数据行
    data_lines = []
    for row in rows:
        line = '|' + '|'.join(f" {str(cell):<{col_widths[i]}} " for i, cell in enumerate(row)) + '|'
        data_lines.append(line)
    
    return '\n'.join([header_line, sep] + data_lines)


def csv_table(headers: List[str], rows: List[List[Any]], delimiter: str = ',') -> str:
    """
    CSV表格
    
    Args:
        headers: 表头
        rows: 行数据
        delimiter: 分隔符
        
    Returns:
        CSV字符串
    """
    lines = []
    
    # 表头
    lines.append(delimiter.join(str(h) for h in headers))
    
    # 数据行
    for row in rows:
        lines.append(delimiter.join(str(cell) for cell in row))
    
    return '\n'.join(lines)


def html_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    HTML表格
    
    Args:
        headers: 表头
        rows: 行数据
        
    Returns:
        HTML表格字符串
    """
    lines = ['<table>']
    
    # 表头
    lines.append('  <thead><tr>')
    for h in headers:
        lines.append(f'    <th>{h}</th>')
    lines.append('  </tr></thead>')
    
    # 数据行
    lines.append('  <tbody>')
    for row in rows:
        lines.append('    <tr>')
        for cell in row:
            lines.append(f'      <td>{cell}</td>')
        lines.append('    </tr>')
    lines.append('  </tbody>')
    
    lines.append('</table>')
    return '\n'.join(lines)


# 导出
__all__ = [
    "ascii_table",
    "markdown_table",
    "csv_table",
    "html_table",
]
