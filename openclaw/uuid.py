"""
UUID - 唯一标识符
基于 Claude Code uuid.ts 设计

UUID工具。
"""
import uuid as _uuid
from typing import List


def generate() -> str:
    """
    生成UUID
    
    Returns:
        UUID字符串
    """
    return str(_uuid.uuid4())


def generate_v1() -> str:
    """
    生成UUID v1（基于时间）
    
    Returns:
        UUID字符串
    """
    return str(_uuid.uuid1())


def from_string(value: str) -> _uuid.UUID:
    """
    从字符串创建UUID
    
    Args:
        value: UUID字符串
        
    Returns:
        UUID对象
    """
    return _uuid.UUID(value)


def is_valid(value: str) -> bool:
    """
    检查是否为有效UUID
    
    Args:
        value: 字符串
        
    Returns:
        是否有效
    """
    try:
        _uuid.UUID(value)
        return True
    except ValueError:
        return False


def uuid3(namespace: str, name: str) -> str:
    """
    生成UUID v3（基于MD5）
    
    Args:
        namespace: 命名空间
        name: 名称
        
    Returns:
        UUID字符串
    """
    return str(_uuid.uuid3(_uuid.NAMESPACE_DNS, f"{namespace}:{name}"))


def uuid5(namespace: str, name: str) -> str:
    """
    生成UUID v5（基于SHA-1）
    
    Args:
        namespace: 命名空间
        name: 名称
        
    Returns:
        UUID字符串
    """
    return str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"{namespace}:{name}"))


def get_parts(uuid_str: str) -> dict:
    """
    获取UUID各部分
    
    Args:
        uuid_str: UUID字符串
        
    Returns:
        各部分的字典
    """
    u = _uuid.UUID(uuid_str)
    return {
        'time_low': u.time_low,
        'time_mid': u.time_mid,
        'time_hi_version': u.time_hi_version,
        'clock_seq_hi': u.clock_seq_hi,
        'clock_seq_low': u.clock_seq_low,
        'node': u.node,
    }


def get_time(uuid_str: str) -> float:
    """
    获取UUID v1的时间戳
    
    Args:
        uuid_str: UUID字符串
        
    Returns:
        时间戳
    """
    u = _uuid.UUID(uuid_str)
    return u.time


class UUIDGenerator:
    """
    UUID生成器
    """
    
    def __init__(self, version: int = 4):
        """
        Args:
            version: 版本 (1, 3, 4, 5)
        """
        self._version = version
    
    def generate(self, namespace: str = None, name: str = None) -> str:
        """
        生成UUID
        
        Args:
            namespace: 命名空间（v3/v5需要）
            name: 名称（v3/v5需要）
            
        Returns:
            UUID字符串
        """
        if self._version == 1:
            return generate_v1()
        if self._version == 3:
            return uuid3(namespace or 'dns', name or '')
        if self._version == 5:
            return uuid5(namespace or 'dns', name or '')
        return generate()


# 导出
__all__ = [
    "generate",
    "generate_v1",
    "from_string",
    "is_valid",
    "uuid3",
    "uuid5",
    "get_parts",
    "get_time",
    "UUIDGenerator",
]
