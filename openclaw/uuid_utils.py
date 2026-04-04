"""
UUID Utilities - UUID工具
基于 Claude Code uuid.ts 设计

提供UUID生成和验证。
"""
import re
import uuid as uuid_lib


# UUID格式正则
UUID_REGEX = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


def validate_uuid(maybe_uuid: str) -> str | None:
    """
    验证UUID格式
    
    Args:
        maybe_uuid: 要验证的值
        
    Returns:
        有效的UUID或None
    """
    if not isinstance(maybe_uuid, str):
        return None
    
    if UUID_REGEX.match(maybe_uuid):
        return maybe_uuid
    
    return None


def create_uuid() -> str:
    """
    生成新UUID
    
    Returns:
        UUID字符串
    """
    return str(uuid_lib.uuid4())


def create_agent_id(label: str = "") -> str:
    """
    生成Agent ID
    
    格式: a{label-}{16 hex chars}
    
    Args:
        label: 可选的标签
        
    Returns:
        Agent ID字符串
    """
    import secrets
    suffix = secrets.token_hex(8)
    if label:
        return f"a{label}-{suffix}"
    return f"a{suffix}"


# 导出
__all__ = [
    "validate_uuid",
    "create_uuid",
    "create_agent_id",
    "UUID_REGEX",
]
