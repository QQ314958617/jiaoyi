"""
YAML - YAML解析
基于 Claude Code yaml.ts 设计

YAML工具。
"""
from typing import Any


def parse(yaml_str: str) -> Any:
    """
    解析YAML
    
    Args:
        yaml_str: YAML字符串
        
    Returns:
        Python对象
    """
    try:
        import ruamel.yaml as ruamel
        from io import StringIO
        yaml = ruamel.YAML()
        return yaml.load(StringIO(yaml_str))
    except ImportError:
        import yaml
        return yaml.safe_load(yaml_str)


def dump(obj: Any) -> str:
    """
    转为YAML字符串
    
    Args:
        obj: Python对象
        
    Returns:
        YAML字符串
    """
    try:
        import ruamel.yaml as ruamel
        from io import StringIO
        yaml = ruamel.YAML()
        buf = StringIO()
        yaml.dump(obj, buf)
        return buf.getvalue()
    except ImportError:
        import yaml
        return yaml.dump(obj, default_flow_style=False)


def to_json(yaml_str: str) -> str:
    """YAML转JSON"""
    import json
    return json.dumps(parse(yaml_str), indent=2)


def from_json(json_str: str) -> str:
    """JSON转YAML"""
    import json
    return dump(json.loads(json_str))


# 导出
__all__ = [
    "parse",
    "dump",
    "to_json",
    "from_json",
]
