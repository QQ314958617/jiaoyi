"""
Query - 查询
基于 Claude Code query.ts 设计

查询字符串解析工具。
"""
import urllib.parse
from typing import Any, Dict, List


def parse(query: str) -> Dict[str, Any]:
    """
    解析查询字符串
    
    Args:
        query: 查询字符串 (a=1&b=2)
        
    Returns:
        参数字典
    """
    if not query:
        return {}
    
    # 移除开头的?
    if query.startswith('?'):
        query = query[1:]
    
    result = {}
    
    for key, value in urllib.parse.parse_qsl(query):
        # 尝试转换类型
        if value.isdigit():
            value = int(value)
        elif value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        
        result[key] = value
    
    return result


def build(params: Dict[str, Any]) -> str:
    """
    构建查询字符串
    
    Args:
        params:参数字典
        
    Returns:
        查询字符串
    """
    # 过滤None值
    filtered = {k: v for k, v in params.items() if v is not None}
    return urllib.parse.urlencode(filtered)


def add_param(query: str, key: str, value: Any) -> str:
    """
    添加参数
    
    Args:
        query: 现有查询字符串
        key: 参数名
        value: 参数值
        
    Returns:
        新查询字符串
    """
    params = parse(query)
    params[key] = value
    return build(params)


def remove_param(query: str, key: str) -> str:
    """
    移除参数
    
    Args:
        query: 现有查询字符串
        key: 参数名
        
    Returns:
        新查询字符串
    """
    params = parse(query)
    params.pop(key, None)
    return build(params)


def get_param(query: str, key: str, default: Any = None) -> Any:
    """
    获取参数
    
    Args:
        query: 查询字符串
        key: 参数名
        default: 默认值
        
    Returns:
        参数值
    """
    params = parse(query)
    return params.get(key, default)


def has_param(query: str, key: str) -> bool:
    """检查参数是否存在"""
    params = parse(query)
    return key in params


# 导出
__all__ = [
    "parse",
    "build",
    "add_param",
    "remove_param",
    "get_param",
    "has_param",
]
