"""
IDGenerator - ID生成器
基于 Claude Code idGenerator.ts 设计

各种ID生成策略。
"""
import threading
import time
from typing import Optional


class SequentialID:
    """
    顺序ID生成器
    
    生成递增的整数ID。
    """
    
    def __init__(self, start: int = 1):
        self._current = start
        self._lock = threading.Lock()
    
    def next(self) -> int:
        """获取下一个ID"""
        with self._lock:
            id = self._current
            self._current += 1
            return id
    
    def peek(self) -> int:
        """查看下一个ID"""
        with self._lock:
            return self._current
    
    def reset(self, start: int = 1) -> None:
        """重置"""
        with self._lock:
            self._current = start


class TimestampID:
    """
    时间戳ID生成器
    
    基于时间戳生成唯一ID。
    """
    
    def __init__(self, prefix: str = ''):
        self._prefix = prefix
        self._counter = 0
        self._last_time = 0
        self._lock = threading.Lock()
    
    def next(self) -> str:
        """获取下一个ID"""
        with self._lock:
            now = int(time.time() * 1000)
            
            if now == self._last_time:
                self._counter += 1
            else:
                self._counter = 0
                self._last_time = now
            
            return f"{self._prefix}{now}:{self._counter}"


class UUIDID:
    """
    UUID ID生成器
    """
    
    def __init__(self):
        import uuid
        self._uuid = uuid
    
    def next(self) -> str:
        """获取下一个UUID"""
        return str(self._uuid.uuid4())


class ShortID:
    """
    短ID生成器
    
    生成URL安全的短ID。
    """
    
    def __init__(self, length: int = 8):
        import base64
        import secrets
        self._length = length
        self._secrets = secrets
        self._base64 = base64
    
    def next(self) -> str:
        """获取下一个短ID"""
        # 使用URL安全的随机字节
        token = self._secrets.token_urlsafe(self._length)
        return token[:self._length]


class ULID:
    """
    ULID (Universally Unique Lexicographically Sortable Identifier)
    
    时间戳 + 随机字符串，可排序。
    """
    
    ENCODING = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
    ENCODING_LEN = len(ENCODING)
    
    @staticmethod
    def _encode_time(time_ms: int, length: int) -> str:
        """编码时间部分"""
        result = []
        for _ in range(length):
            result.append(ULID.ENCODING[time_ms % ULID.ENCODING_LEN])
            time_ms //= ULID.ENCODING_LEN
        return ''.join(reversed(result))
    
    @staticmethod
    def _encode_random(length: int) -> str:
        """编码随机部分"""
        import secrets
        result = []
        remaining = length
        
        while remaining > 0:
            rand = secrets.randbelow(ULID.ENCODING_LEN ** min(remaining, 10))
            encode_len = min(remaining, 10)
            
            for _ in range(encode_len):
                remaining -= 1
                result.append(ULID.ENCODING[rand % ULID.ENCODING_LEN])
                rand //= ULID.ENCODING_LEN
        
        return ''.join(result)
    
    @classmethod
    def next(cls) -> str:
        """生成ULID"""
        now = int(time.time() * 1000)
        time_part = cls._encode_time(now, 10)
        rand_part = cls._encode_random(16)
        return f"{time_part}{rand_part}"


# 全局生成器
_global_sequential = SequentialID()
_global_timestamp = TimestampID()
_global_uuid = UUIDID()
_global_short = ShortID()


def next_id(type: str = 'auto') -> str:
    """
    生成ID
    
    Args:
        type: ID类型 ('auto', 'uuid', 'short', 'ulid', 'timestamp')
        
    Returns:
        ID字符串
    """
    if type == 'uuid':
        return _global_uuid.next()
    elif type == 'short':
        return _global_short.next()
    elif type == 'ulid':
        return ULID.next()
    elif type == 'timestamp':
        return _global_timestamp.next()
    else:
        # auto: 顺序ID
        return str(_global_sequential.next())


# 导出
__all__ = [
    "SequentialID",
    "TimestampID",
    "UUIDID",
    "ShortID",
    "ULID",
    "next_id",
]
