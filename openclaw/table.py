"""
Table - 表格
基于 Claude Code table.ts 设计

表格工具。
"""
from typing import List, Dict, Any


def format_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    格式化表格
    
    Args:
        headers: 表头
        rows: 行数据
    """
    if not headers:
        return ""
    
    # 计算每列宽度
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # 分隔线
    sep = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'
    
    # 表头
    header_line = '|' + '|'.join(f" {h}{' ' * (col_widths[i] - len(h))}" 
                                   for i, h in enumerate(headers)) + '|'
    
    # 数据行
    data_lines = []
    for row in rows:
        line = '|' + '|'.join(f" {str(cell)}{' ' * (col_widths[i] - len(str(cell)))}"
                                for i, cell in enumerate(row)) + '|'
        data_lines.append(line)
    
    return '\n'.join([sep, header_line, sep] + data_lines + [sep])


def markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    Markdown表格
    """
    if not headers:
        return ""
    
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    def fmt_cell(cell, width):
        s = str(cell)
        return s + ' ' * (width - len(s))
    
    # 表头
    header_line = '| ' + ' | '.join(fmt_cell(h, col_widths[i]) for i, h in enumerate(headers)) + ' |'
    
    # 分隔线
    sep_line = '| ' + ' | '.join('-' * w for w in col_widths) + ' |'
    
    # 数据行
    data_lines = []
    for row in rows:
        line = '| ' + ' | '.join(fmt_cell(cell, col_widths[i]) for i, cell in enumerate(row)) + ' |'
        data_lines.append(line)
    
    return '\n'.join([header_line, sep_line] + data_lines)


def tsv_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    TSV表格（制表符分隔）
    """
    if not headers:
        return ""
    
    lines = ['\t'.join(headers)]
    for row in rows:
        lines.append('\t'.join(str(cell) for cell in row))
    
    return '\n'.join(lines)


# 导出
__all__ = [
    "format_table",
    "markdown_table",
    "tsv_table",
]
