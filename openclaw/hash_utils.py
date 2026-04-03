"""
OpenClaw Hash Utilities
====================
Inspired by Claude Code's src/utils/hash.ts.

哈希工具，支持：
1. djb2 哈希（非加密）
2. 内容哈希（变更检测）
3. 增量哈希
4. 对哈希
"""

from __future__ import annotations

import hashlib, hashlib as hl
from typing import Union

# ============================================================================
# djb2 哈希
# ============================================================================

def djb2_hash(text: str) -> int:
    """
    DJB2 哈希算法（非加密）
    
    返回 32 位有符号整数
    在不同运行时一致
    
    Example:
        djb2_hash("hello") → 邦定
    """
    hash_val = 0
    for char in text:
        hash_val = ((hash_val << 5) - hash_val + ord(char)) & 0xFFFFFFFF
    # 转换为有符号整数
    if hash_val & 0x80000000:
        hash_val -= 0x100000000
    return hash_val

def djb2_hash_unsigned(text: str) -> int:
    """DJB2 哈希（无符号）"""
    hash_val = 0
    for char in text:
        hash_val = ((hash_val << 5) - hash_val + ord(char)) & 0xFFFFFFFF
    return hash_val

# ============================================================================
# 内容哈希
# ============================================================================

def hash_content(content: str, algorithm: str = "sha256") -> str:
    """
    对内容进行哈希
    
    用于变更检测（非加密安全）
    
    Args:
        content: 内容
        algorithm: 算法（md5/sha1/sha256）
    
    Example:
        hash_content("hello") → "2cf24dba5fb..."
    """
    h = hashlib.new(algorithm)
    h.update(content.encode("utf-8"))
    return h.hexdigest()

def hash_bytes(data: bytes, algorithm: str = "sha256") -> str:
    """对字节数据进行哈希"""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()

def md5_hash(content: str) -> str:
    """MD5 哈希（快速但不安全）"""
    return hash_content(content, "md5")

def sha256_hash(content: str) -> str:
    """SHA-256 哈希"""
    return hash_content(content, "sha256")

# ============================================================================
# 增量哈希
# ============================================================================

class IncrementalHash:
    """
    增量哈希器
    
    支持多次 update，最后一次性获取摘要
    
    Example:
        hasher = IncrementalHash()
        hasher.update("hello")
        hasher.update(" ")
        hasher.update("world")
        print(hasher.hexdigest())
    """
    
    def __init__(self, algorithm: str = "sha256"):
        self._hasher = hashlib.new(algorithm)
    
    def update(self, data: Union[str, bytes]) -> 'IncrementalHash':
        """添加数据"""
        if isinstance(data, str):
            data = data.encode("utf-8")
        self._hasher.update(data)
        return self
    
    def digest(self) -> bytes:
        """获取摘要（原始字节）"""
        return self._hasher.digest()
    
    def hexdigest(self) -> str:
        """获取十六进制摘要"""
        return self._hasher.hexdigest()
    
    def copy(self) -> 'IncrementalHash':
        """复制当前状态"""
        new_hasher = IncrementalHash.__new__(IncrementalHash)
        new_hasher._hasher = self._hasher.copy()
        return new_hasher

# ============================================================================
# 对哈希
# ============================================================================

def hash_pair(a: str, b: str, algorithm: str = "sha256") -> str:
    """
    对两个字符串进行哈希（不使用临时拼接字符串）
    
    使用增量哈希实现，避免内存分配
    
    Example:
        hash_pair("a", "b") → 邦定
    """
    h = hashlib.new(algorithm)
    h.update(a.encode("utf-8"))
    h.update(b.encode("utf-8"))
    return h.hexdigest()

def hash_pair_separated(a: str, b: str, sep: str = "\0", 
                       algorithm: str = "sha256") -> str:
    """
    使用分隔符对两个字符串进行哈希
    
    Args:
        a: 第一个字符串
        b: 第二个字符串
        sep: 分隔符
        algorithm: 哈希算法
    """
    h = hashlib.new(algorithm)
    h.update(a.encode("utf-8"))
    h.update(sep.encode("utf-8"))
    h.update(b.encode("utf-8"))
    return h.hexdigest()

# ============================================================================
# 文件哈希
# ============================================================================

def hash_file(file_path: str, algorithm: str = "sha256", 
             chunk_size: int = 8192) -> str:
    """
    计算文件哈希
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法
        chunk_size: 每次读取的块大小
    
    Returns:
        十六进制哈希字符串
    """
    h = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    
    return h.hexdigest()

# ============================================================================
# HMAC
# ============================================================================

def hmac_hash(content: str, key: str, algorithm: str = "sha256") -> str:
    """
    HMAC 哈希（带密钥的消息认证码）
    
    Args:
        content: 消息内容
        key: 密钥
        algorithm: 哈希算法
    
    Returns:
        HMAC 十六进制字符串
    """
    import hmac as hmac_module
    return hmac_module.new(
        key.encode("utf-8"),
        content.encode("utf-8"),
        digestmod=algorithm
    ).hexdigest()

def verify_hmac(content: str, mac: str, key: str, 
                algorithm: str = "sha256") -> bool:
    """验证 HMAC"""
    expected = hmac_hash(content, key, algorithm)
    import hmac as hmac_module
    return hmac_module.compare_digest(expected, mac)

# ============================================================================
# 便捷函数
# ============================================================================

def short_hash(content: str, length: int = 8) -> str:
    """
    生成短哈希（取前 N 位）
    
    Example:
        short_hash("hello world") → "2cf24dba"
    """
    return sha256_hash(content)[:length]

def hash_to_int(content: str) -> int:
    """将哈希转换为整数"""
    full_hash = sha256_hash(content)
    return int(full_hash, 16)

def int_to_hash(n: int, length: int = 64) -> str:
    """将整数转换为哈希格式字符串"""
    hex_str = format(n, "x").zfill(length)
    return hex_str
