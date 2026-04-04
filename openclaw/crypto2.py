"""
Crypto2 - 加密
基于 Claude Code crypto.ts 设计

加密工具。
"""
import hashlib
import hmac
import secrets
import base64
from typing import bytes


def sha256(data: str) -> str:
    """
    SHA256哈希
    
    Args:
        data: 字符串数据
        
    Returns:
        十六进制哈希
    """
    return hashlib.sha256(data.encode()).hexdigest()


def sha256_bytes(data: bytes) -> bytes:
    """SHA256字节哈希"""
    return hashlib.sha256(data).digest()


def md5(data: str) -> str:
    """MD5哈希"""
    return hashlib.md5(data.encode()).hexdigest()


def hmac_sha256(key: str, data: str) -> str:
    """
    HMAC SHA256
    
    Args:
        key: 密钥
        data: 数据
        
    Returns:
        十六进制MAC
    """
    return hmac.new(
        key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


def hmac_sha256_bytes(key: bytes, data: bytes) -> bytes:
    """HMAC SHA256字节"""
    return hmac.new(key, data, hashlib.sha256).digest()


def base64_encode(data: bytes) -> str:
    """Base64编码"""
    return base64.b64encode(data).decode()


def base64_decode(data: str) -> bytes:
    """Base64解码"""
    return base64.b64decode(data)


def base64url_encode(data: bytes) -> str:
    """Base64URL编码"""
    return base64.urlsafe_b64encode(data).decode().rstrip('=')


def base64url_decode(data: str) -> bytes:
    """Base64URL解码"""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def random_hex(length: int = 32) -> str:
    """
    随机十六进制字符串
    
    Args:
        length: 长度
        
    Returns:
        随机hex字符串
    """
    return secrets.token_hex(length // 2)


def random_bytes(length: int = 32) -> bytes:
    """随机字节"""
    return secrets.token_bytes(length)


def random_urlsafe(length: int = 32) -> str:
    """随机URL安全字符串"""
    return secrets.token_urlsafe(length)


def generate_secret(length: int = 32) -> str:
    """生成安全密钥"""
    return random_hex(length)


# 导出
__all__ = [
    "sha256",
    "sha256_bytes",
    "md5",
    "hmac_sha256",
    "hmac_sha256_bytes",
    "base64_encode",
    "base64_decode",
    "base64url_encode",
    "base64url_decode",
    "random_hex",
    "random_bytes",
    "random_urlsafe",
    "generate_secret",
]
