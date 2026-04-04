"""
Hash - 哈希
基于 Claude Code hash.ts 设计

哈希函数工具。
"""
import hashlib
import hmac
from typing import Any


def md5(data: str) -> str:
    """
    MD5哈希
    
    Args:
        data: 字符串
        
    Returns:
        十六进制哈希
    """
    return hashlib.md5(data.encode()).hexdigest()


def sha1(data: str) -> str:
    """
    SHA1哈希
    
    Args:
        data: 字符串
        
    Returns:
        十六进制哈希
    """
    return hashlib.sha1(data.encode()).hexdigest()


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


def hmac_sha512(secret: str, message: str) -> str:
    """
    HMAC-SHA512
    
    Args:
        secret: 密钥
        message: 消息
        
    Returns:
        十六进制MAC
    """
    return hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha512
    ).hexdigest()


def hash_bytes(data: bytes, algorithm: str = 'sha256') -> str:
    """
    字节数据哈希
    
    Args:
        data: 字节数据
        algorithm: 算法 ('md5', 'sha1', 'sha256', 'sha512')
        
    Returns:
        十六进制哈希
    """
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def file_hash(path: str, algorithm: str = 'sha256') -> str:
    """
    文件哈希
    
    Args:
        path: 文件路径
        algorithm: 算法
        
    Returns:
        十六进制哈希
    """
    h = hashlib.new(algorithm)
    
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    
    return h.hexdigest()


def hash_password(password: str, salt: str = None) -> str:
    """
    密码哈希（简单版）
    
    Args:
        password: 密码
        salt: 盐值
        
    Returns:
        哈希值
    """
    import secrets
    
    if salt is None:
        salt = secrets.token_hex(16)
    
    data = f"{salt}{password}"
    hashed = sha256(data)
    
    return f"{salt}${hashed}"


def verify_password(password: str, hashed: str) -> bool:
    """
    验证密码
    
    Args:
        password: 密码
        hashed: 哈希值 (格式: salt$hash)
        
    Returns:
        是否匹配
    """
    parts = hashed.split('$')
    if len(parts) != 2:
        return False
    
    salt, stored_hash = parts
    return sha256(f"{salt}{password}") == stored_hash


def uuid5(namespace: str, name: str) -> str:
    """
    生成UUID v5（基于命名空间的UUID）
    
    Args:
        namespace: 命名空间
        name: 名称
        
    Returns:
        UUID字符串
    """
    import uuid
    ns_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, namespace)
    return str(uuid.uuid5(ns_uuid, name))


# 导出
__all__ = [
    "md5",
    "sha1",
    "sha256",
    "sha512",
    "hmac_sha256",
    "hmac_sha512",
    "hash_bytes",
    "file_hash",
    "hash_password",
    "verify_password",
    "uuid5",
]
