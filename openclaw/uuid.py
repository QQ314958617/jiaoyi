"""
UUID - 唯一标识符
基于 Claude Code uuid.ts 设计

UUID生成和验证工具。
"""
import uuid
import re


UUID_REGEX = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


def generate_uuid() -> str:
    """
    生成UUID v4
    
    Returns:
        UUID字符串
    """
    return str(uuid.uuid4())


def generate_uuid_v4() -> str:
    """
    生成UUID v4
    
    Returns:
        UUID字符串
    """
    return generate_uuid()


def generate_short_id(length: int = 8) -> str:
    """
    生成短ID
    
    Args:
        length: 长度
        
    Returns:
        短ID字符串
    """
    return uuid.uuid4().hex[:length]


def is_valid_uuid(value: str) -> bool:
    """
    检查是否为有效的UUID
    
    Args:
        value: 值
        
    Returns:
        是否有效
    """
    if not value:
        return False
    return bool(UUID_REGEX.match(value))


def validate_uuid(value: str) -> str:
    """
    验证并返回UUID
    
    Args:
        value: 值
        
    Returns:
        有效UUID
        
    Raises:
        ValueError: 无效UUID
    """
    if not is_valid_uuid(value):
        raise ValueError(f"Invalid UUID: {value}")
    return value.lower()


# 导出
__all__ = [
    "generate_uuid",
    "generate_uuid_v4",
    "generate_short_id",
    "is_valid_uuid",
    "validate_uuid",
]
