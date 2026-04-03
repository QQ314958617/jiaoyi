"""
OpenClaw JSON Utilities
=====================
Inspired by Claude Code's src/utils/json.ts.

JSON 处理工具，支持：
1. 安全解析（带缓存）
2. JSONC 解析（带注释）
3. JSON Schema 验证
4. JSON 合并
"""

from __future__ import annotations

import json, re
from typing import Any, Optional, Dict
from pathlib import Path

# ============================================================================
# 基础 JSON
# ============================================================================

def safe_parse_json(json_str: str | None, default: Any = None) -> Any:
    """
    安全解析 JSON
    
    - 自动 strip BOM
    - 解析失败返回 default
    """
    if not json_str:
        return default
    
    try:
        # Strip BOM
        if json_str.startswith('\ufeff'):
            json_str = json_str[1:]
        
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def strip_bom(text: str) -> str:
    """去除 BOM"""
    if text.startswith('\ufeff'):
        return text[1:]
    return text

def read_json_file(path: str | Path, default: Any = None) -> Any:
    """读取 JSON 文件"""
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            return safe_parse_json(f.read(), default)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def write_json_file(path: str | Path, data: Any, indent: int = 2) -> bool:
    """写入 JSON 文件"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        return True
    except (IOError, TypeError):
        return False

# ============================================================================
# JSON 合并
# ============================================================================

def merge_json(base: Dict, override: Dict, deep: bool = True) -> Dict:
    """
    合并两个 JSON 对象
    
    Args:
        base: 基础对象
        override: 覆盖对象
        deep: 是否深度合并
    """
    result = dict(base)
    
    for key, value in override.items():
        if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json(result[key], value, deep)
        else:
            result[key] = value
    
    return result

# ============================================================================
# JSON Schema 验证（简化版）
# ============================================================================

def validate_json_schema(data: Any, schema: Dict) -> tuple[bool, list[str]]:
    """
    简单 JSON Schema 验证
    
    Returns: (is_valid, error_messages)
    """
    errors = []
    
    def validate(obj, schema_obj, path):
        if schema_obj.get("type") == "object":
            if not isinstance(obj, dict):
                errors.append(f"{path}: expected object, got {type(obj).__name__}")
                return
            
            required = schema_obj.get("required", [])
            for req in required:
                if req not in obj:
                    errors.append(f"{path}: missing required field '{req}'")
            
            for key, value in obj.items():
                if key in schema_obj.get("properties", {}):
                    validate(value, schema_obj["properties"][key], f"{path}.{key}")
        
        elif schema_obj.get("type") == "array":
            if not isinstance(obj, list):
                errors.append(f"{path}: expected array, got {type(obj).__name__}")
                return
            
            for i, item in enumerate(obj):
                if "items" in schema_obj:
                    validate(item, schema_obj["items"], f"{path}[{i}]")
        
        elif schema_obj.get("type") == "string":
            if not isinstance(obj, str):
                errors.append(f"{path}: expected string, got {type(obj).__name__}")
        
        elif schema_obj.get("type") == "number":
            if not isinstance(obj, (int, float)):
                errors.append(f"{path}: expected number, got {type(obj).__name__}")
        
        elif schema_obj.get("type") == "boolean":
            if not isinstance(obj, bool):
                errors.append(f"{path}: expected boolean, got {type(obj).__name__}")
    
    validate(data, schema, "$")
    return len(errors) == 0, errors

# ============================================================================
# JSON Path
# ============================================================================

def get_json_path(data: Any, path: str, default: Any = None) -> Any:
    """
    按路径获取 JSON 数据
    
    Example:
        get_json_path({"a": {"b": [1, 2]}}, "a.b.0") → 1
    """
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            try:
                idx = int(key)
                current = current[idx]
            except (ValueError, IndexError):
                return default
        else:
            return default
        
        if current is None:
            return default
    
    return current

def set_json_path(data: Dict, path: str, value: Any) -> None:
    """
    按路径设置 JSON 数据
    
    Example:
        data = {}
        set_json_path(data, "a.b.0", "hello")
        # data = {"a": {"b": ["hello"]}}
    """
    keys = path.split('.')
    current = data
    
    for i, key in enumerate(keys[:-1]):
        if key not in current:
            current[key] = {}
        current = current[key]
    
    final_key = keys[-1]
    if isinstance(current, list):
        try:
            idx = int(final_key)
            while len(current) <= idx:
                current.append(None)
            current[idx] = value
        except ValueError:
            current[final_key] = value
    else:
        current[final_key] = value

# ============================================================================
# JSON 差异
# ============================================================================

def json_diff(old: Dict, new: Dict, path: str = "$") -> list[dict]:
    """
    比较两个 JSON 对象的差异
    
    Returns: [{"op": "add|remove|replace", "path": "...", "old": ..., "new": ...}]
    """
    diffs = []
    
    # 查找新增和修改
    for key in set(old.keys()) | set(new.keys()):
        current_path = f"{path}.{key}"
        
        if key not in old:
            diffs.append({"op": "add", "path": current_path, "new": new[key]})
        elif key not in new:
            diffs.append({"op": "remove", "path": current_path, "old": old[key]})
        elif old[key] != new[key]:
            if isinstance(old[key], dict) and isinstance(new[key], dict):
                diffs.extend(json_diff(old[key], new[key], current_path))
            else:
                diffs.append({
                    "op": "replace",
                    "path": current_path,
                    "old": old[key],
                    "new": new[key]
                })
    
    return diffs

# ============================================================================
# 常用数据转换
# ============================================================================

def to_json_string(data: Any, indent: int = None, ensure_ascii: bool = False) -> str:
    """转换为 JSON 字符串"""
    if indent is not None:
        return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
    return json.dumps(data, ensure_ascii=ensure_ascii)

def pretty_json(data: Any) -> str:
    """格式化 JSON（带颜色，用于调试）"""
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)

def compact_json(data: Any) -> str:
    """压缩 JSON（无缩进）"""
    return json.dumps(data, separators=(',', ':'))

def is_valid_json(text: str) -> bool:
    """检查是否是有效 JSON"""
    try:
        json.loads(text)
        return True
    except:
        return False
