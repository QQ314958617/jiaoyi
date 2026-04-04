"""
Chart - 图表
基于 Claude Code chart.ts 设计

图表工具。
"""


def bar_chart(data: dict, width: int = 40) -> str:
    """
    简单条形图
    
    Args:
        data: {"label": value}
        width: 最大宽度
    """
    if not data:
        return ""
    
    max_val = max(data.values())
    if max_val == 0:
        max_val = 1
    
    lines = []
    for label, value in data.items():
        bar_len = int(width * value / max_val)
        bar = '█' * bar_len
        lines.append(f"{label:10} {bar} {value}")
    
    return '\n'.join(lines)


def h_bar_chart(data: dict, height: int = 10) -> str:
    """
    水平条形图
    
    Args:
        data: {"label": value}
        height: 高度
    """
    if not data:
        return ""
    
    lines = []
    max_val = max(data.values())
    if max_val == 0:
        max_val = 1
    
    for label, value in data.items():
        percentage = value / max_val * 100
        lines.append(f"{label:10} | {'█' * int(percentage / 5):20} {percentage:.1f}%")
    
    return '\n'.join(lines)


def sparkline(values: list, width: int = 20) -> str:
    """
    迷你走势图
    
    Args:
        values: 数值列表
        width: 宽度
    """
    if not values:
        return ""
    
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val
    
    if range_val == 0:
        range_val = 1
    
    blocks = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    
    result = []
    for v in values:
        idx = int((v - min_val) / range_val * (len(blocks) - 1))
        result.append(blocks[idx])
    
    return ''.join(result)


def pie_chart(data: dict) -> str:
    """
    简单饼图（字符模式）
    """
    if not data:
        return ""
    
    total = sum(data.values())
    if total == 0:
        return ""
    
    chars = ['●', '◐', '◑', '○']
    lines = []
    
    for i, (label, value) in enumerate(data.items()):
        pct = value / total * 100
        char = chars[i % len(chars)]
        lines.append(f"{char} {label}: {pct:.1f}%")
    
    return '\n'.join(lines)


# 导出
__all__ = [
    "bar_chart",
    "h_bar_chart",
    "sparkline",
    "pie_chart",
]
