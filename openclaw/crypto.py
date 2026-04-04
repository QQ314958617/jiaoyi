"""
Crypto - 加密
基于 Claude Code crypto.ts 设计

加密工具。
"""
import base64
import hashlib
import hmac
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


def generate_key() -> str:
    """生成Fernet密钥"""
    return Fernet.generate_key().decode()


def encrypt(data: str, key: str) -> str:
    """
    加密数据
    
    Args:
        data: 明文
        key: 密钥
        
    Returns:
        密文(base64)
    """
    f = Fernet(key.encode())
    return f.encrypt(data.encode()).decode()


def decrypt(data: str, key: str) -> str:
    """
    解密数据
    
    Args:
        data: 密文
        key: 密钥
        
    Returns:
        明文
    """
    f = Fernet(key.encode())
    return f.decrypt(data.encode()).decode()


def derive_key(password: str, salt: bytes = None) -> tuple:
    """
    从密码派生密钥
    
    Args:
        password: 密码
        salt: 盐值（可选）
        
    Returns:
        (密钥, 盐值)
    """
    if salt is None:
        salt = secrets.token_bytes(16)
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key.decode(), salt


def aes_encrypt(data: str, key: str) -> str:
    """AES加密（使用Fernet）"""
    return encrypt(data, key)


def aes_decrypt(data: str, key: str) -> str:
    """AES解密"""
    return decrypt(data, key)


def xor_encrypt(data: str, key: str) -> str:
    """
    XOR加密（简单）
    
    Args:
        data: 明文
        key: 密钥
        
    Returns:
        密文
    """
    result = []
    for i, c in enumerate(data):
        k = key[i % len(key)]
        result.append(chr(ord(c) ^ ord(k)))
    return base64.b64encode(''.join(result).encode()).decode()


def xor_decrypt(data: str, key: str) -> str:
    """XOR解密"""
    data = base64.b64decode(data).decode()
    result = []
    for i, c in enumerate(data):
        k = key[i % len(key)]
        result.append(chr(ord(c) ^ ord(k)))
    return ''.join(result)


# 导出
__all__ = [
    "generate_key",
    "encrypt",
    "decrypt",
    "derive_key",
    "aes_encrypt",
    "aes_decrypt",
    "xor_encrypt",
    "xor_decrypt",
]
