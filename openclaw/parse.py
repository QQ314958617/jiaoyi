"""
Parse - 解析
基于 Claude Code parse.ts 设计

解析工具。
"""
import json
import re
from typing import Any, Dict, List, Optional


def parse_json(text: str, default: Any = None) -> Any:
    """
    解析JSON
    
    Args:
        text: JSON字符串
        default: 失败默认值
        
    Returns:
        解析结果或默认值
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def parse_query(query: str) -> Dict[str, str]:
    """
    解析查询字符串
    
    Args:
        query: 查询字符串 (a=1&b=2)
        
    Returns:
        参数字典
    """
    import urllib.parse
    return dict(urllib.parse.parse_qsl(query))


def parse_url(url: str) -> Dict[str, Any]:
    """
    解析URL
    
    Args:
        url: URL字符串
        
    Returns:
        URL组件字典
    """
    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    return {
        'scheme': parsed.scheme,
        'netloc': parsed.netloc,
        'path': parsed.path,
        'params': parsed.params,
        'query': dict(urllib.parse.parse_qsl(parsed.query)),
        'fragment': parsed.fragment,
    }


def parse_header(header: str) -> Dict[str, str]:
    """
    解析HTTP头
    
    Args:
        header: 头字符串
        
    Returns:
        头字典
    """
    result = {}
    parts = header.split(';')
    
    for part in parts:
        part = part.strip()
        if '=' in part:
            key, value = part.split('=', 1)
            result[key.strip()] = value.strip().strip('"')
    
    return result


def parse_json_lines(text: str) -> List[Any]:
    """
    解析JSON行
    
    Args:
        text: 多行JSON
        
    Returns:
        对象列表
    """
    results = []
    
    for line in text.strip().split('\n'):
        line = line.strip()
        if line:
            obj = parse_json(line)
            if obj is not None:
                results.append(obj)
    
    return results


def parse_csv_line(line: str, delimiter: str = ',') -> List[str]:
    """
    解析CSV行
    
    Args:
        line: CSV行
        delimiter: 分隔符
        
    Returns:
        字段列表
    """
    result = []
    current = []
    in_quotes = False
    
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == delimiter and not in_quotes:
            result.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    
    result.append(''.join(current).strip())
    return result


def parse_ini(text: str) -> Dict[str, Dict[str, str]]:
    """
    解析INI文本
    
    Args:
        text: INI文本
        
    Returns:
        {section: {key: value}}
    """
    result = {}
    current_section = ''
    
    for line in text.strip().split('\n'):
        line = line.strip()
        
        if not line or line.startswith(';') or line.startswith('#'):
            continue
        
        if line.startswith('[') and line.endswith(']'):
            current_section = line[1:-1]
            result[current_section] = {}
            continue
        
        if '=' in line and current_section:
            key, value = line.split('=', 1)
            result[current_section][key.strip()] = value.strip()
    
    return result


def parse_key_values(text: str, delimiter: str = '=') -> Dict[str, str]:
    """
    解析键值对
    
    Args:
        text: 键值对文本
        delimiter: 分隔符
        
    Returns:
        键值字典
    """
    result = {}
    
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if delimiter in line:
            key, value = line.split(delimiter, 1)
            result[key.strip()] = value.strip()
    
    return result


def parse_env(text: str) -> Dict[str, str]:
    """解析环境变量文本"""
    result = {}
    
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if '=' in line:
            key, value = line.split('=', 1)
            result[key.strip()] = value.strip().strip('"').strip("'")
    
    return result


def parse_number(text: str) -> Optional[float]:
    """解析数字"""
    try:
        return float(text.strip())
    except (ValueError, AttributeError):
        return None


def parse_int(text: str) -> Optional[int]:
    """解析整数"""
    try:
        return int(text.strip())
    except (ValueError, AttributeError):
        return None


def parse_bool(text: str) -> Optional[bool]:
    """解析布尔值"""
    text = text.strip().lower()
    
    if text in ('true', '1', 'yes', 'on'):
        return True
    if text in ('false', '0', 'no', 'off'):
        return False
    
    return None


# 导出
__all__ = [
    "parse_json",
    "parse_query",
    "parse_url",
    "parse_header",
    "parse_json_lines",
    "parse_csv_line",
    "parse_ini",
    "parse_key_values",
    "parse_env",
    "parse_number",
    "parse_int",
    "parse_bool",
]
