"""
OpenClaw ID Generator
====================
Inspired by Claude Code's src/utils/uuid.ts.

ID 生成器，支持：
1. UUID v4
2. 短 ID（8位/12位十六进制）
3. 带前缀的 ID
4. 时间戳 ID
5. 雪花 ID（分布式）
"""

from __future__ import annotations

import hashlib, os, time
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional

# ============================================================================
# 基础 UUID
# ============================================================================

def uuid4() -> str:
    """生成 UUID v4"""
    import uuid
    return str(uuid.uuid4())

def uuid4_hex() -> str:
    """生成 UUID v4（无连字符）"""
    import uuid
    return uuid.uuid4().hex

def is_valid_uuid(value: str) -> bool:
    """检查是否是有效的 UUID"""
    import uuid
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

# ============================================================================
# 短 ID
# ============================================================================

def short_id(length: int = 8) -> str:
    """生成短 ID（十六进制）"""
    return os.urandom(length // 2 + 1).hex()[:length]

def short_id_time(prefix: str = "") -> str:
    """生成带时间戳的短 ID"""
    ts = int(time.time() * 1000) & 0xFFFFFFFF
    sid = os.urandom(4).hex()
    return f"{prefix}{ts:08x}{sid}" if prefix else f"{ts:08x}{sid}"

# ============================================================================
# Agent ID（Claude Code 风格）
# ============================================================================

def create_agent_id(label: Optional[str] = None) -> str:
    """
    创建 Agent ID
    
    格式：a{label-}{16 hex chars} 或 a{16 hex chars}
    
    Example: aa3f2c1b4d5e6f7a, acompact-a3f2c1b4d5e6f7a
    """
    suffix = os.urandom(8).hex()
    if label:
        return f"a{label}-{suffix}"
    return f"a{suffix}"

# ============================================================================
# Task ID
# ============================================================================

def create_task_id(prefix: str = "task") -> str:
    """创建任务 ID"""
    ts = int(time.time() * 1000) & 0xFFFFFFFF
    rnd = os.urandom(4).hex()
    return f"{prefix}-{ts:08x}-{rnd}"

# ============================================================================
# 交易专用 ID
# ============================================================================

class TradeIDGenerator:
    """
    交易 ID 生成器
    
    生成格式：
    - 订单: ORD-{timestamp}-{random}
    - 持仓: POS-{timestamp}-{random}
    - 流水: TRX-{timestamp}-{random}
    - 信号: SIG-{timestamp}-{random}
    """
    
    _counter = 0
    _lock = threading.Lock()
    _last_ts = 0
    
    @classmethod
    def _get_counter(cls) -> int:
        """获取计数器（同一毫秒内递增）"""
        now = int(time.time() * 1000)
        with cls._lock:
            if now == cls._last_ts:
                cls._counter += 1
            else:
                cls._counter = 0
                cls._last_ts = now
            return cls._counter
    
    @classmethod
    def order_id(cls) -> str:
        """订单 ID"""
        ts = int(time.time() * 1000)
        cnt = cls._get_counter()
        rnd = os.urandom(3).hex()
        return f"ORD-{ts:013x}-{cnt:02x}-{rnd}"
    
    @classmethod
    def position_id(cls) -> str:
        """持仓 ID"""
        ts = int(time.time() * 1000)
        rnd = os.urandom(4).hex()
        return f"POS-{ts:013x}-{rnd}"
    
    @classmethod
    def trade_id(cls) -> str:
        """交易流水 ID"""
        ts = int(time.time() * 1000)
        rnd = os.urandom(4).hex()
        return f"TRX-{ts:013x}-{rnd}"
    
    @classmethod
    def signal_id(cls) -> str:
        """信号 ID"""
        ts = int(time.time() * 1000)
        rnd = os.urandom(3).hex()
        return f"SIG-{ts:013x}-{rnd}"

# ============================================================================
# 雪花 ID
# ============================================================================

class SnowflakeID:
    """
    Twitter Snowflake ID 生成器
    
    分布式唯一 ID，64 位：
    - 1 位：符号（0）
    - 41 位：时间戳（毫秒）
    - 10 位：机器 ID
    - 12 位：序列号
    """
    
    def __init__(self, machine_id: int = 0):
        self.machine_id = machine_id & 0x3FF  # 10 位
        self.epoch = 1609459200000  # 2021-01-01 00:00:00 UTC
        self._last_ts = 0
        self._sequence = 0
        self._lock = threading.Lock()
    
    def generate(self) -> int:
        """生成雪花 ID"""
        with self._lock:
            now = int(time.time() * 1000)
            
            if now == self._last_ts:
                self._sequence = (self._sequence + 1) & 0xFFF
                if self._sequence == 0:
                    # 序列溢出，等待下一毫秒
                    while now == self._last_ts:
                        now = int(time.time() * 1000)
            else:
                self._sequence = 0
            
            self._last_ts = now
            
            ts = now - self.epoch
            return (ts << 22) | (self.machine_id << 12) | self._sequence
    
    def generate_str(self) -> str:
        """生成雪花 ID（字符串）"""
        return str(self.generate())

# ============================================================================
# 会话 ID
# ============================================================================

def create_session_id() -> str:
    """创建会话 ID"""
    return f"sess-{os.urandom(16).hex()}"

def create_session_id_short() -> str:
    """创建短会话 ID"""
    return f"sess-{os.urandom(8).hex()}"

# ============================================================================
# Hash ID
# ============================================================================

def hash_id(data: str, length: int = 12) -> str:
    """基于哈希生成 ID"""
    h = hashlib.sha256(data.encode()).hexdigest()
    return h[:length]

def hash_id_md5(data: str, length: int = 12) -> str:
    """基于 MD5 生成 ID（更快）"""
    h = hashlib.md5(data.encode()).hexdigest()
    return h[:length]

# ============================================================================
# 全局生成器
# ============================================================================

_trade_gen = TradeIDGenerator()
_snowflake = SnowflakeID()

def new_order_id() -> str:
    """新订单 ID"""
    return _trade_gen.order_id()

def new_position_id() -> str:
    """新持仓 ID"""
    return _trade_gen.position_id()

def new_trade_id() -> str:
    """新交易流水 ID"""
    return _trade_gen.trade_id()

def new_signal_id() -> str:
    """新信号 ID"""
    return _trade_gen.signal_id()

def new_snowflake_id() -> int:
    """新雪花 ID"""
    return _snowflake.generate()

def new_snowflake_str() -> str:
    """新雪花 ID（字符串）"""
    return _snowflake.generate_str()
