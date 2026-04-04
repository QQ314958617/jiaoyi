"""
YAML - YAML解析
基于 Claude Code yaml.ts 设计

YAML解析封装。
"""
from typing import Any, Optional

# 尝试使用PyYAML
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_yaml(input_str: str) -> Optional[Any]:
    """
    解析YAML字符串
    
    Args:
        input_str: YAML字符串
        
    Returns:
        解析后的对象
    """
    if not HAS_YAML:
        return None
    
    try:
        return yaml.safe_load(input_str)
    except Exception:
        return None


def dump_yaml(data: Any) -> str:
    """
    将对象序列化为YAML
    
    Args:
        data: 数据
        
    Returns:
        YAML字符串
    """
    if not HAS_YAML:
        return str(data)
    
    try:
        return yaml.dump(data, allow_unicode=True, sort_keys=False)
    except Exception:
        return str(data)


# 导出
__all__ = [
    "parse_yaml",
    "dump_yaml",
    "HAS_YAML",
]
