"""
Parser - 解析器
基于 Claude Code parser.ts 设计

字符串解析工具。
"""
import re
from typing import Any, Callable, Dict, List, Optional, Tuple


class Parser:
    """
    简单解析器
    
    基于正则的字符串解析。
    """
    
    def __init__(self, pattern: str, flags: int = 0):
        """
        Args:
            pattern: 正则模式
            flags: 正则标志
        """
        self._pattern = re.compile(pattern, flags)
    
    def parse(self, text: str) -> Optional[Dict[str, str]]:
        """
        解析文本
        
        Args:
            text: 要解析的文本
            
        Returns:
            命名组字典
        """
        match = self._pattern.match(text)
        if match:
            return match.groupdict()
        return None
    
    def find_all(self, text: str) -> List[Dict[str, str]]:
        """
        查找所有匹配
        
        Args:
            text: 要解析的文本
            
        Returns:
            匹配列表
        """
        return [m.groupdict() for m in self._pattern.finditer(text)]


def parse_key_value(text: str, delimiter: str = '=') -> Dict[str, str]:
    """
    解析键值对
    
    Args:
        text: 文本（每行一个键值对）
        delimiter: 分隔符
        
    Returns:
        键值对字典
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


def parse_query_string(query: str) -> Dict[str, str]:
    """
    解析查询字符串
    
    Args:
        query: 查询字符串 (a=1&b=2)
        
    Returns:
        参数字典
    """
    import urllib.parse
    return dict(urllib.parse.parse_qsl(query))


def parse_json_lines(text: str) -> List[Any]:
    """
    解析JSON行
    
    Args:
        text: 多行JSON文本
        
    Returns:
        对象列表
    """
    result = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if line:
            import json
            result.append(json.loads(line))
    return result


def parse_ini_section(line: str) -> Optional[str]:
    """
    解析INI节头
    
    Args:
        line: 行
        
    Returns:
        节名或None
    """
    if line.startswith('[') and line.endswith(']'):
        return line[1:-1]
    return None


def parse_ini(text: str) -> Dict[str, Dict[str, str]]:
    """
    解析INI文本
    
    Args:
        text: INI文本
        
    Returns:
        {节名: {键: 值}}
    """
    result: Dict[str, Dict[str, str]] = {}
    current_section = ''
    
    for line in text.strip().split('\n'):
        line = line.strip()
        
        if not line or line.startswith(';') or line.startswith('#'):
            continue
        
        section = parse_ini_section(line)
        if section:
            current_section = section
            if current_section not in result:
                result[current_section] = {}
            continue
        
        if '=' in line and current_section:
            key, value = line.split('=', 1)
            result[current_section][key.strip()] = value.strip()
    
    return result


# 导出
__all__ = [
    "Parser",
    "parse_key_value",
    "parse_csv_line",
    "parse_query_string",
    "parse_json_lines",
    "parse_ini_section",
    "parse_ini",
]
