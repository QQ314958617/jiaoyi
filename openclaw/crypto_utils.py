"""
OpenClaw Crypto Utilities
====================
Inspired by Claude Code's src/services/oauth/crypto.ts.

加密工具，支持：
1. PKCE (Proof Key for Code Exchange)
2. OAuth 状态生成
3. 密码学安全随机数
4. Base64 URL 安全编码
"""

from __future__ import annotations

import secrets, hashlib, base64
from typing import Optional

# ============================================================================
# Base64 URL 安全编码
# ============================================================================

def base64url_encode(data: bytes) -> str:
    """
    Base64 URL 安全编码
    
    - 替换 + → -
    - 替换 / → _
    - 移除尾部 =
    
    Example:
        base64url_encode(b"Hello") → "SGVsbG8"
    """
    return (
        base64.urlsafe_b64encode(data)
        .decode("ascii")
        .rstrip("=")
        .replace("+", "-")
        .replace("/", "_")
    )

def base64url_decode(data: str) -> bytes:
    """
    Base64 URL 安全解码
    
    Example:
        base64url_decode("SGVsbG8") → b"Hello"
    """
    # 恢复标准 Base64
    data = data.replace("-", "+").replace("_", "/")
    
    # 添加填充
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    
    return base64.urlsafe_b64decode(data)

# ============================================================================
# PKCE (Proof Key for Code Exchange)
# ============================================================================

def generate_code_verifier(length: int = 64) -> str:
    """
    生成 OAuth Code Verifier
    
    RFC 7636 规范：
    - 最小 43 字符
    - 最大 128 字符
    - 仅允许 [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"
    
    Args:
        length: 随机字节数（默认64，产生约86字符）
    
    Example:
        code_verifier = generate_code_verifier()
    """
    # 生成随机字节
    random_bytes = secrets.token_bytes(length)
    
    # 使用 URL 安全 Base64 编码
    return base64url_encode(random_bytes)

def generate_code_challenge(verifier: str) -> str:
    """
    从 Code Verifier 生成 Code Challenge
    
    S256 方法：SHA256 哈希后 Base64 URL 编码
    
    Args:
        verifier: Code Verifier
    
    Example:
        code_challenge = generate_code_challenge(code_verifier)
    """
    # SHA256 哈希
    hash = hashlib.sha256(verifier.encode("ascii")).digest()
    
    # Base64 URL 安全编码
    return base64url_encode(hash)

def generate_pkce_pair() -> tuple[str, str]:
    """
    生成 PKCE 密钥对 (verifier, challenge)
    
    Returns:
        (code_verifier, code_challenge)
    
    Example:
        verifier, challenge = generate_pkce_pair()
    """
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    return verifier, challenge

# ============================================================================
# OAuth 状态
# ============================================================================

def generate_state(length: int = 32) -> str:
    """
    生成 OAuth 状态参数
    
    用于防止 CSRF 攻击
    
    Args:
        length: 随机字节数
    
    Example:
        state = generate_state()
    """
    return base64url_encode(secrets.token_bytes(length))

# ============================================================================
# 密码学安全随机数
# ============================================================================

def random_bytes(n: int) -> bytes:
    """
    生成密码学安全的随机字节
    
    Args:
        n: 字节数
    
    Example:
        random_bytes(16) → b"\\x8c\\x15..."
    """
    return secrets.token_bytes(n)

def random_int(max_value: int) -> int:
    """
    生成密码学安全的随机整数 [0, max_value)
    
    Example:
        random_int(100) → 42
    """
    return secrets.randbelow(max_value)

def random_hex(n: int) -> str:
    """
    生成随机十六进制字符串
    
    Args:
        n: 字符数（字节数的2倍）
    
    Example:
        random_hex(32) → "8c15..."
    """
    return secrets.token_hex(n)

def token_urlsafe(n: int = 32) -> str:
    """
    生成 URL 安全的随机字符串
    
    Args:
        n: 字节数
    
    Example:
        token_urlsafe(32) → "S2K..."
    """
    return secrets.token_urlsafe(n)

# ============================================================================
# 密钥派生
# ============================================================================

def derive_key(password: str, salt: bytes, iterations: int = 100000,
              key_length: int = 32) -> bytes:
    """
    从密码派生密钥（PBKDF2）
    
    Args:
        password: 密码
        salt: 盐
        iterations: 迭代次数
        key_length: 密钥长度
    
    Returns:
        派生的密钥
    """
    import hashlib
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
        dklen=key_length
    )

def generate_salt(length: int = 16) -> bytes:
    """
    生成随机盐
    
    Example:
        salt = generate_salt()
    """
    return secrets.token_bytes(length)

# ============================================================================
# HMAC
# ============================================================================

def hmac_sha256(key: bytes, message: bytes) -> bytes:
    """
    HMAC-SHA256
    
    Args:
        key: 密钥
        message: 消息
    
    Returns:
        HMAC 摘要
    """
    import hmac as hmac_module
    return hmac_module.new(key, message, hashlib.sha256).digest()

def hmac_sha256_hex(key: bytes, message: bytes) -> str:
    """HMAC-SHA256（十六进制）"""
    return hmac_sha256(key, message).hex()

# ============================================================================
# 密码哈希
# ============================================================================

def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """
    哈希密码
    
    使用 PBKDF2-SHA256
    
    Args:
        password: 密码
        salt: 盐（如果为 None 则自动生成）
    
    Returns:
        (hash_hex, salt_hex)
    """
    if salt is None:
        salt = generate_salt()
    
    key = derive_key(password, salt)
    
    return key.hex(), salt.hex()

def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """
    验证密码
    
    Args:
        password: 密码
        hash_hex: 哈希（十六进制）
        salt_hex: 盐（十六进制）
    
    Returns:
        是否匹配
    """
    salt = bytes.fromhex(salt_hex)
    expected_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(hash_hex, expected_hash)
