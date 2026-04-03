"""
OpenClaw YAML Utilities
====================
Inspired by Claude Code's src/utils/yaml.ts.

YAML 解析和序列化，支持：
1. YAML 解析
2. YAML 序列化
3. 安全加载
"""

from __future__ import annotations

import yaml
from typing import Any, Optional

# ============================================================================
# 解析
# ============================================================================

def parse_yaml(content: str) -> Any:
    """
    解析 YAML 字符串
    
    Example:
        data = parse_yaml("name: test\\nvalue: 123")
    """
    return yaml.safe_load(content)

def parse_yaml_all(content: str) -> Any:
    """
    解析 YAML（支持多文档）
    
    Returns:
        如果是单文档，返回单个对象
        如果是多文档，返回列表
    """
    docs = list(yaml.safe_load_all(content))
    if len(docs) == 1:
        return docs[0]
    return docs

# ============================================================================
# 序列化
# ============================================================================

def to_yaml(data: Any, default_flow_style: bool = False, 
           sort_keys: bool = False) -> str:
    """
    转换为 YAML 字符串
    
    Args:
        data: Python 对象
        default_flow_style: False = 块式输出, True = 流动式
        sort_keys: 是否按键排序
    """
    return yaml.dump(data, 
                    allow_unicode=True,
                    default_flow_style=default_flow_style,
                    sort_keys=sort_keys,
                    indent=2)

def to_yaml_safe(data: Any, default_flow_style: bool = False) -> str:
    """安全转换为 YAML（使用 safe_dump）"""
    return yaml.safe_dump(data,
                         allow_unicode=True,
                         default_flow_style=default_flow_style,
                         indent=2)

# ============================================================================
# 文件操作
# ============================================================================

def read_yaml_file(path: str) -> Any:
    """
    读取 YAML 文件
    
    Returns:
        文件内容（Python 对象）
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return None
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML: {e}")

def write_yaml_file(path: str, data: Any, 
                   default_flow_style: bool = False) -> bool:
    """
    写入 YAML 文件
    
    Returns:
        True if successful
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, 
                         allow_unicode=True,
                         default_flow_style=default_flow_style,
                         indent=2)
        return True
    except (IOError, yaml.YAMLError):
        return False

# ============================================================================
# 合并和更新
# ============================================================================

def merge_yaml(base: dict, override: dict, deep: bool = True) -> dict:
    """
    合并两个 YAML 对象
    
    Args:
        base: 基础对象
        override: 覆盖对象
        deep: 是否深度合并
    """
    import copy
    
    if not deep:
        return {**base, **override}
    
    result = copy.deepcopy(base)
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_yaml(result[key], value, deep=True)
        else:
            result[key] = copy.deepcopy(value)
    
    return result

# ============================================================================
# 类型转换
# ============================================================================

def yaml_to_json(data: Any) -> str:
    """YAML 对象转 JSON 字符串"""
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)

def json_to_yaml(data: str) -> Any:
    """JSON 字符串转 YAML 对象"""
    import json
    return yaml.safe_load(json.loads(data))

# ============================================================================
# Schema 验证（简单实现）
# ============================================================================

def validate_yaml_schema(data: Any, schema: dict) -> tuple[bool, list[str]]:
    """
    简单 YAML Schema 验证
    
    Args:
        data: YAML 数据
        schema: Schema 定义
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # 检查必需字段
    required = schema.get("required", [])
    if isinstance(data, dict):
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
    
    # 检查类型
    expected_type = schema.get("type")
    if expected_type:
        type_map = {
            "string": str,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        
        if expected_type in type_map:
            expected = type_map[expected_type]
            if not isinstance(data, expected):
                errors.append(f"Expected {expected_type}, got {type(data).__name__}")
    
    return len(errors) == 0, errors
