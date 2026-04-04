"""
TOML - TOML解析
基于 Claude Code toml.ts 设计

TOML解析工具（简化实现）。
"""
import re
from datetime import datetime
from typing import Any, Dict, List


def parse_toml(text: str) -> Dict[str, Any]:
    """
    解析TOML
    
    Args:
        text: TOML文本
        
    Returns:
        解析后的字典
    """
    result = {}
    current_section = None
    current_table = result
    
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行和注释
        if not line or line.startswith('#'):
            continue
        
        # 节头
        if line.startswith('['):
            if line.startswith('[['):
                # 数组表
                table_name = line[2:-2].strip()
                if table_name not in result:
                    result[table_name] = []
                current_section = table_name
                current_table = {}
                result[table_name].append(current_table)
            else:
                # 普通节
                section_name = line[1:-1].strip()
                if section_name not in result:
                    result[section_name] = {}
                current_section = section_name
                current_table = result[section_name]
            continue
        
        # 键值对
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = _parse_value(value.strip())
            
            if current_section:
                current_table[key] = value
            else:
                result[key] = value
    
    return result


def _parse_value(value: str) -> Any:
    """解析TOML值"""
    value = value.strip()
    
    # 字符串
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    
    # 多行字符串
    if value.startswith('"""'):
        return value[3:-3].strip()
    
    # 布尔值
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # 整数
    try:
        return int(value)
    except ValueError:
        pass
    
    # 浮点数
    try:
        return float(value)
    except ValueError:
        pass
    
    # 日期
    date_pattern = r'\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)?'
    if re.match(date_pattern, value):
        try:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            pass
    
    # 数组
    if value.startswith('[') and value.endswith(']'):
        return _parse_array(value[1:-1])
    
    return value


def _parse_array(text: str) -> List[Any]:
    """解析数组"""
    if not text.strip():
        return []
    
    result = []
    current = ''
    depth = 0
    in_string = False
    
    for char in text:
        if char in ('"', "'") and (not current or current[-1] != '\\'):
            in_string = not in_string
        
        if not in_string:
            if char == '[':
                depth += 1
            elif char == ']':
                depth -= 1
        
        if char == ',' and depth == 0 and not in_string:
            result.append(_parse_value(current.strip()))
            current = ''
        else:
            current += char
    
    if current.strip():
        result.append(_parse_value(current.strip()))
    
    return result


# 导出
__all__ = [
    "parse_toml",
]
