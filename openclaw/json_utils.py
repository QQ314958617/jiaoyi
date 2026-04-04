"""
JSON Utilities - JSON处理工具
基于 Claude Code json.ts 设计

提供安全的JSON解析、JSONC支持（带注释的JSON），
以及JSON修改功能。
"""
import json
from functools import lru_cache
from typing import Any, Optional

from .errors import log_error


# JSON解析缓存最大键大小
PARSE_CACHE_MAX_KEY_BYTES = 8 * 1024


def strip_bom(s: str) -> str:
    """
    移除UTF-8 BOM
    
    Args:
        s: 字符串
        
    Returns:
        移除BOM后的字符串
    """
    if s.startswith('\ufeff'):
        return s[1:]
    return s


def safe_parse_json(
    json_str: Optional[str],
    should_log_error: bool = True,
) -> Any:
    """
    安全解析JSON
    
    Args:
        json_str: JSON字符串
        should_log_error: 是否记录错误
        
    Returns:
        解析后的对象，失败返回None
    """
    if not json_str:
        return None
    
    try:
        return json.loads(strip_bom(json_str))
    except Exception as e:
        if should_log_error:
            log_error(f"JSON parse error: {e}")
        return None


def safe_parse_jsonc(json_str: Optional[str]) -> Any:
    """
    安全解析JSONC（带注释的JSON）
    
    用于VS Code配置文件等支持注释的JSON格式。
    
    Args:
        json_str: JSON字符串
        
    Returns:
        解析后的对象，失败返回None
    """
    if not json_str:
        return None
    
    try:
        content = strip_bom(json_str)
        
        # 移除注释和尾随逗号
        lines = []
        for line in content.split('\n'):
            # 移除 // 注释
            if '#' in line:
                # 字符串内的#不算
                in_string = False
                escaped = False
                for i, c in enumerate(line):
                    if escaped:
                        escaped = False
                        continue
                    if c == '"' and not in_string:
                        in_string = True
                    elif c == '\\':
                        escaped = True
                    elif c == '#' and in_string:
                        line = line[:i]
                        break
                else:
                    # 字符串外找到#，截断
                    for i, c in enumerate(line):
                        if c == '"':
                            in_string = not in_string
                        elif c == '#' and not in_string:
                            line = line[:i].rstrip()
                            break
            
            # 移除尾随逗号
            line = line.rstrip()
            if line.endswith(','):
                line = line[:-1].rstrip()
            
            lines.append(line)
        
        result = ''.join(lines)
        return json.loads(result)
        
    except Exception as e:
        log_error(f"JSONC parse error: {e}")
        return None


@lru_cache(maxsize=50)
def _parse_json_cached(json_str: str) -> Optional[Any]:
    """缓存的JSON解析"""
    try:
        return json.loads(strip_bom(json_str))
    except Exception:
        return None


def parse_json_cached(json_str: str) -> Optional[Any]:
    """
    带缓存的JSON解析（小字符串）
    
    Args:
        json_str: JSON字符串
        
    Returns:
        解析后的对象
    """
    if len(json_str) > PARSE_CACHE_MAX_KEY_BYTES:
        return safe_parse_json(json_str, False)
    return _parse_json_cached(json_str)


def modify_json(
    content: str,
    path: list,
    value: Any,
) -> str:
    """
    修改JSON字符串中的某个路径的值
    
    Args:
        content: JSON字符串
        path: 路径列表，如 ["key", "nested", "value"]
        value: 新的值
        
    Returns:
        修改后的JSON字符串
    """
    try:
        data = safe_parse_json(content)
        if data is None:
            return content
        
        # 遍历路径
        current = data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 设置值
        current[path[-1]] = value
        
        return json.dumps(data, indent=2)
        
    except Exception as e:
        log_error(f"modify_json error: {e}")
        return content


def add_to_json_array(
    content: str,
    array_path: list,
    new_item: Any,
) -> str:
    """
    向JSON数组添加元素
    
    Args:
        content: JSON字符串
        array_path: 数组的路径
        new_item: 要添加的元素
        
    Returns:
        修改后的JSON字符串
    """
    try:
        data = safe_parse_json(content)
        if data is None:
            return content
        
        # 遍历路径
        current = data
        for key in array_path:
            if key not in current:
                current[key] = []
            current = current[key]
        
        # 添加元素
        if isinstance(current, list):
            current.append(new_item)
        
        return json.dumps(data, indent=2)
        
    except Exception as e:
        log_error(f"add_to_json_array error: {e}")
        return content


# 导出
__all__ = [
    "strip_bom",
    "safe_parse_json",
    "safe_parse_jsonc",
    "parse_json_cached",
    "modify_json",
    "add_to_json_array",
    "PARSE_CACHE_MAX_KEY_BYTES",
]
