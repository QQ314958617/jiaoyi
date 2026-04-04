"""
Chart - 图表
基于 Claude Code chart.ts 设计

简单图表工具。
"""


def bar_chart(data: dict, width: int = 40, height: int = 10) -> str:
    """
    条形图
    
    Args:
        data: {标签: 数值}
        width: 图表宽度
        height: 图表高度
        
    Returns:
        ASCII条形图
    """
    if not data:
        return ""
    
    max_val = max(data.values())
    if max_val == 0:
        max_val = 1
    
    lines = []
    labels = list(data.keys())
    values = list(data.values())
    
    for i in range(height, 0, -1):
        line = ""
        threshold = (i / height) * max_val
        
        for val in values:
            if val >= threshold:
                bar_width = max(1, int(width * val / max_val / len(values)))
                line += "█" * bar_width
            else:
                line += " " * (width // len(values))
        
        lines.append(line)
    
    # 标签
    label_line = ""
    for label in labels:
        label_line += label[:width // len(labels)].center(width // len(values))
    
    lines.append(label_line)
    
    # 数值
    value_line = ""
    for val in values:
        value_line += str(val)[:width // len(values)].center(width // len(values))
    
    lines.append(value_line)
    
    return '\n'.join(lines)


def horizontal_bar_chart(data: dict, width: int = 40) -> str:
    """
    水平条形图
    
    Args:
        data: {标签: 数值}
        width: 条形宽度
        
    Returns:
        ASCII水平条形图
    """
    if not data:
        return ""
    
    max_val = max(data.values())
    if max_val == 0:
        max_val = 1
    
    lines = []
    
    for label, value in data.items():
        bar_len = int(width * value / max_val)
        bar = "█" * bar_len
        lines.append(f"{label:10} {bar} {value}")
    
    return '\n'.join(lines)


def line_chart(points: list, width: int = 50, height: int = 10) -> str:
    """
    折线图
    
    Args:
        points: [(x, y)] 或 [y值列表]
        width: 宽度
        height: 高度
        
    Returns:
        ASCII折线图
    """
    if not points:
        return ""
    
    # 如果是简单列表，转为索引
    if all(isinstance(p, (int, float)) for p in points):
        points = list(enumerate(points))
    
    y_values = [p[1] for p in points]
    min_y = min(y_values)
    max_y = max(y_values)
    
    if max_y == min_y:
        max_y = min_y + 1
    
    # 创建网格
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # 绘制折线
    for i, (x, y) in enumerate(points):
        if len(points) > 1:
            x_pos = int((i / (len(points) - 1)) * (width - 1))
        else:
            x_pos = width // 2
        y_pos = height - 1 - int((y - min_y) / (max_y - min_y) * (height - 1))
        y_pos = max(0, min(height - 1, y_pos))
        grid[y_pos][x_pos] = '●'
        
        # 连接点
        if i > 0:
            prev_x, prev_y = points[i - 1]
            prev_x_pos = int((i - 1) / (len(points) - 1)) * (width - 1) if len(points) > 1 else width // 2
            prev_y_pos = height - 1 - int((prev_y - min_y) / (max_y - min_y) * (height - 1))
            prev_y_pos = max(0, min(height - 1, prev_y_pos))
            
            # 简单连接
            x1, x2 = min(x_pos, prev_x_pos), max(x_pos, prev_x_pos)
            for x in range(x1, x2 + 1):
                if 0 <= x < width and 0 <= prev_y_pos < height:
                    if grid[prev_y_pos][x] == ' ':
                        grid[prev_y_pos][x] = '─'
    
    # 输出
    lines = [''.join(row) for row in grid]
    return '\n'.join(lines)


def pie_chart(data: dict, size: int = 4) -> str:
    """
    饼图（简化）
    
    Args:
        data: {标签: 数值}
        size: 显示大小
        
    Returns:
        饼图字符串
    """
    if not data:
        return ""
    
    total = sum(data.values())
    if total == 0:
        return ""
    
    lines = []
    for label, value in data.items():
        percent = value / total * 100
        bar = "█" * int(percent / 5)
        lines.append(f"{label}: {bar} {percent:.1f}%")
    
    return '\n'.join(lines)


# 导出
__all__ = [
    "bar_chart",
    "horizontal_bar_chart",
    "line_chart",
    "pie_chart",
]
