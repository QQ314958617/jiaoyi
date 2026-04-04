"""
Zod to JSON Schema - Zod schema转换
基于 Claude Code zodToJsonSchema.ts 设计

Zod schema转换为JSON Schema。
"""
from typing import Any, Dict, Optional


# JSON Schema类型
JsonSchema7Type = Dict[str, Any]


# 简化的Zod类型映射
ZOD_TYPE_MAP = {
    'string': {'type': 'string'},
    'number': {'type': 'number'},
    'integer': {'type': 'integer'},
    'boolean': {'type': 'boolean'},
    'array': {'type': 'array'},
    'object': {'type': 'object'},
    'null': {'type': 'null'},
}


def zod_to_json_schema(schema: Any) -> JsonSchema7Type:
    """
    将Zod schema转换为JSON Schema
    
    这是一个简化实现，实际的Zod有更复杂的类型系统。
    
    Args:
        schema: Zod schema对象
        
    Returns:
        JSON Schema字典
    """
    if schema is None:
        return {}
    
    # 如果是字典，直接返回
    if isinstance(schema, dict):
        return schema
    
    # 检查是否是Zod schema对象
    schema_type = getattr(schema, '_type', None) or getattr(schema, 'type', None)
    
    if schema_type in ZOD_TYPE_MAP:
        return ZOD_TYPE_MAP[schema_type]
    
    # 尝试获取JSON Schema表示
    if hasattr(schema, 'to_json_schema'):
        return schema.to_json_schema()
    
    if hasattr(schema, 'toJSON'):
        result = schema.toJSON()
        if isinstance(result, dict):
            return result
    
    # 回退到通用对象
    return {
        'type': 'object',
        'properties': {},
    }


def infer_json_schema_from_data(data: Any) -> JsonSchema7Type:
    """
    从数据推断JSON Schema
    
    Args:
        data: 示例数据
        
    Returns:
        JSON Schema
    """
    if data is None:
        return {'type': 'null'}
    
    if isinstance(data, bool):
        return {'type': 'boolean'}
    
    if isinstance(data, int):
        return {'type': 'integer'}
    
    if isinstance(data, float):
        return {'type': 'number'}
    
    if isinstance(data, str):
        return {'type': 'string'}
    
    if isinstance(data, list):
        if data:
            return {
                'type': 'array',
                'items': infer_json_schema_from_data(data[0]),
            }
        return {'type': 'array', 'items': {}}
    
    if isinstance(data, dict):
        properties = {
            key: infer_json_schema_from_data(value)
            for key, value in data.items()
        }
        return {
            'type': 'object',
            'properties': properties,
        }
    
    return {}


# 导出
__all__ = [
    "JsonSchema7Type",
    "zod_to_json_schema",
    "infer_json_schema_from_data",
]
