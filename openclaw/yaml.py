"""
YAML - YAML解析
基于 Claude Code yaml.ts 设计

YAML解析工具（简化实现）。
"""
from typing import Any, Dict, List


def parse_yaml(text: str) -> Any:
    """
    解析YAML
    
    Args:
        text: YAML文本
        
    Returns:
        解析后的对象
    """
    lines = text.split('\n')
    result = _parse_lines(lines)
    return result


def _parse_lines(lines: List[str]) -> Any:
    """解析YAML行"""
    result = None
    current_key = None
    current_indent = 0
    indent_stack = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 跳过空行和注释
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue
        
        # 计算缩进
        indent = len(line) - len(line.lstrip())
        
        # 处理列表项
        if line.strip().startswith('- '):
            item_value = line.strip()[2:].strip()
            
            if result is None:
                result = []
            
            if item_value:
                result.append(_parse_value(item_value))
            else:
                # 嵌套结构
                nested_lines = []
                i += 1
                nested_indent = indent + 2
                
                while i < len(lines):
                    next_line = lines[i]
                    if not next_line.strip():
                        i += 1
                        continue
                    
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    if next_indent <= indent:
                        break
                    
                    nested_lines.append(next_line)
                    i += 1
                
                if nested_lines:
                    result.append(_parse_lines(nested_lines))
                else:
                    result.append({})
            
            i += 1
            continue
        
        # 处理键值对
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # 空值
            if not value:
                if result is None:
                    result = {}
                
                # 检查嵌套
                nested_lines = []
                i += 1
                
                while i < len(lines):
                    next_line = lines[i]
                    
                    if not next_line.strip():
                        i += 1
                        continue
                    
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    if next_indent <= indent:
                        break
                    
                    nested_lines.append(next_line)
                    i += 1
                
                if nested_lines:
                    result[key] = _parse_lines(nested_lines)
                else:
                    result[key] = None
            else:
                if result is None:
                    result = {}
                result[key] = _parse_value(value)
        
        i += 1
    
    return result


def _parse_value(value: str) -> Any:
    """解析YAML值"""
    value = value.strip()
    
    # 字符串
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    
    # 布尔值
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() == 'null':
        return None
    
    # 数字
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    return value


def to_yaml(obj: Any, indent: int = 0) -> str:
    """
    对象转YAML
    
    Args:
        obj: 对象
        indent: 当前缩进
        
    Returns:
        YAML字符串
    """
    lines = []
    prefix = '  ' * indent
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(to_yaml(value, indent + 1).split('\n'))
            else:
                lines.append(f"{prefix}{key}: {_format_value(value)}")
    
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(to_yaml(item, indent + 1).split('\n'))
            else:
                lines.append(f"{prefix}- {_format_value(item)}")
    
    else:
        lines.append(f"{prefix}{_format_value(obj)}")
    
    return '\n'.join(lines)


def _format_value(value: Any) -> str:
    """格式化YAML值"""
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        if any(c in value for c in ':{}[],"\'\n'):
            return f'"{value}"'
        return value
    return str(value)


def dump_yaml(obj: Any) -> str:
    """dump_yaml的别名"""
    return to_yaml(obj)


# 导出
__all__ = [
    "parse_yaml",
    "to_yaml",
    "dump_yaml",
]
