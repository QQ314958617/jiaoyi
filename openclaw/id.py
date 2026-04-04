"""
ID - 标识符
基于 Claude Code id.ts 设计

ID生成工具。
"""
import uuid
import hashlib
import time
from typing import Optional


def generate(length: int = 16) -> str:
    """
    生成随机ID
    
    Args:
        length: 长度
        
    Returns:
        ID字符串
    """
    return uuid.uuid4().hex[:length]


def generate_prefix(prefix: str = "") -> str:
    """
    生成带前缀的ID
    
    Args:
        prefix: 前缀
        
    Returns:
        ID字符串
    """
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def from_string(value: str) -> str:
    """
    从字符串生成ID
    
    Args:
        value: 字符串
        
    Returns:
        ID字符串
    """
    return hashlib.md5(value.encode()).hexdigest()[:16]


def from_timestamp(prefix: str = "") -> str:
    """
    基于时间戳生成ID
    
    Args:
        prefix: 前缀
        
    Returns:
        ID字符串
    """
    ts = int(time.time() * 1000)
    return f"{prefix}{ts}"


def sequential(current: int = 0) -> str:
    """
    序列ID
    
    Args:
        current: 当前序号
        
    Returns:
        下一个ID字符串
    """
    return str(current + 1)


def short() -> str:
    """短ID(8字符)"""
    return uuid.uuid4().hex[:8]


def numeric(length: int = 6) -> str:
    """
    数字ID
    
    Args:
        length: 长度
        
    Returns:
        数字字符串
    """
    import random
    return ''.join(random.choice('0123456789') for _ in range(length))


class IDGenerator:
    """
    ID生成器
    """
    
    def __init__(self, prefix: str = ""):
        """
        Args:
            prefix: 前缀
        """
        self._prefix = prefix
        self._counter = 0
    
    def next(self) -> str:
        """下一个ID"""
        self._counter += 1
        return f"{self._prefix}{self._counter}"
    
    def reset(self) -> None:
        """重置计数器"""
        self._counter = 0
    
    @property
    def current(self) -> int:
        return self._counter


def ulid() -> str:
    """
    ULID风格的ID
    
    Returns:
        ULID字符串
    """
    ENCODING = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
    
    now = int(time.time() * 1000)
    time_part = ''
    for _ in range(10):
        time_part = ENCODING[now & 31] + time_part
        now >>= 5
    
    import random
    rand_part = ''.join(random.choice(ENCODING) for _ in range(16))
    
    return time_part + rand_part


# 导出
__all__ = [
    "generate",
    "generate_prefix",
    "from_string",
    "from_timestamp",
    "sequential",
    "short",
    "numeric",
    "IDGenerator",
    "ulid",
]
