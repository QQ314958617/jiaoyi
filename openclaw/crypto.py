"""
Crypto - 加密工具
基于 Claude Code crypto.ts 设计

常用加密工具。
"""
import hashlib
import hmac
import secrets
from typing import Optional


def sha256(data: str) -> str:
    """
    SHA256哈希
    
    Args:
        data: 字符串
        
    Returns:
        十六进制哈希
    """
    return hashlib.sha256(data.encode()).hexdigest()


def sha512(data: str) -> str:
    """
    SHA512哈希
    
    Args:
        data: 字符串
        
    Returns:
        十六进制哈希
    """
    return hashlib.sha512(data.encode()).hexdigest()


def md5(data: str) -> str:
    """
    MD5哈希
    
    Args:
        data: 字符串
        
    Returns:
        十六进制哈希
    """
    return hashlib.md5(data.encode()).hexdigest()


def hmac_sha256(secret: str, message: str) -> str:
    """
    HMAC-SHA256
    
    Args:
        secret: 密钥
        message: 消息
        
    Returns:
        十六进制MAC
    """
    return hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


def generate_token(length: int = 32) -> str:
    """
    生成安全随机Token
    
    Args:
        length: 字节长度
        
    Returns:
        十六进制Token
    """
    return secrets.token_hex(length)


def generate_url_safe_token(length: int = 32) -> str:
    """
    生成URL安全的随机Token
    
    Args:
        length: 字节长度
        
    Returns:
        URL安全Token
    """
    return secrets.token_urlsafe(length)


def constant_time_compare(a: str, b: str) -> bool:
    """
    恒定时间比较
    
    防止时序攻击。
    
    Args:
        a: 字符串1
        b: 字符串2
        
    Returns:
        是否相等
    """
    return hmac.compare_digest(a, b)


# 导出
__all__ = [
    "sha256",
    "sha512",
    "md5",
    "hmac_sha256",
    "generate_token",
    "generate_url_safe_token",
    "constant_time_compare",
]
