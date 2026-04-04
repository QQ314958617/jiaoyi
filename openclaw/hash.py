"""
Hash - 哈希
基于 Claude Code hash.ts 设计

哈希工具。
"""
import hashlib
import hmac


def md5(data: str) -> str:
    """MD5哈希"""
    return hashlib.md5(data.encode()).hexdigest()


def sha1(data: str) -> str:
    """SHA-1哈希"""
    return hashlib.sha1(data.encode()).hexdigest()


def sha256(data: str) -> str:
    """SHA-256哈希"""
    return hashlib.sha256(data.encode()).hexdigest()


def sha512(data: str) -> str:
    """SHA-512哈希"""
    return hashlib.sha512(data.encode()).hexdigest()


def sha3_256(data: str) -> str:
    """SHA3-256哈希"""
    return hashlib.sha3_256(data.encode()).hexdigest()


def sha3_512(data: str) -> str:
    """SHA3-512哈希"""
    return hashlib.sha3_512(data.encode()).hexdigest()


def blake2b(data: str) -> str:
    """BLAKE2b哈希"""
    return hashlib.blake2b(data.encode()).hexdigest()


def blake2s(data: str) -> str:
    """BLAKE2s哈希"""
    return hashlib.blake2s(data.encode()).hexdigest()


def hmac_md5(key: str, data: str) -> str:
    """HMAC-MD5"""
    return hmac.new(key.encode(), data.encode(), hashlib.md5).hexdigest()


def hmac_sha256(key: str, data: str) -> str:
    """HMAC-SHA256"""
    return hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()


def hmac_sha512(key: str, data: str) -> str:
    """HMAC-SHA512"""
    return hmac.new(key.encode(), data.encode(), hashlib.sha512).hexdigest()


def hash_password(password: str, salt: str = None) -> tuple:
    """
    哈希密码
    
    Returns:
        (hash, salt)
    """
    import secrets
    
    if salt is None:
        salt = secrets.token_hex(16)
    
    hash_val = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000
    ).hex()
    
    return hash_val, salt


def verify_password(password: str, hash_val: str, salt: str) -> bool:
    """验证密码"""
    new_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(new_hash, hash_val)


def file_hash(filepath: str, algorithm: str = "sha256") -> str:
    """
    文件哈希
    
    Args:
        filepath: 文件路径
        algorithm: 算法 (md5/sha1/sha256/sha512)
        
    Returns:
        哈希值
    """
    h = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    
    return h.hexdigest()


# 导出
__all__ = [
    "md5",
    "sha1",
    "sha256",
    "sha512",
    "sha3_256",
    "sha3_512",
    "blake2b",
    "blake2s",
    "hmac_md5",
    "hmac_sha256",
    "hmac_sha512",
    "hash_password",
    "verify_password",
    "file_hash",
]
