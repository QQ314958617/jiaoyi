"""
Password - 密码
基于 Claude Code password.ts 设计

密码工具。
"""
import secrets
import string
import hashlib
import hmac


def generate(length: int = 16, 
             uppercase: bool = True,
             lowercase: bool = True,
             digits: bool = True,
             special: bool = True) -> str:
    """
    生成随机密码
    
    Args:
        length: 长度
        uppercase: 包含大写字母
        lowercase: 包含小写字母
        digits: 包含数字
        special: 包含特殊字符
        
    Returns:
        密码字符串
    """
    chars = ''
    
    if uppercase:
        chars += string.ascii_uppercase
    if lowercase:
        chars += string.ascii_lowercase
    if digits:
        chars += string.digits
    if special:
        chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    if not chars:
        chars = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_strong(length: int = 16) -> str:
    """
    生成强密码
    
    包含大小写字母、数字和特殊字符。
    """
    return generate(length, True, True, True, True)


def generate_weak(length: int = 8) -> str:
    """
    生成弱密码
    
    仅包含小写字母和数字。
    """
    chars = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def check_strength(password: str) -> dict:
    """
    检查密码强度
    
    Returns:
        {score: 0-4, feedback: [建议]}
    """
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
    elif len(password) < 6:
        feedback.append("密码太短")
    
    if len(password) >= 12:
        score += 1
    
    if any(c.isupper() for c in password):
        score += 1
    
    if any(c.islower() for c in password):
        score += 1
    
    if any(c.isdigit() for c in password):
        score += 1
    
    special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
    if any(c in special_chars for c in password):
        score += 1
    
    return {
        "score": min(4, score),
        "feedback": feedback
    }


def hash_password(password: str, salt: str = None) -> tuple:
    """
    哈希密码
    
    Args:
        password: 密码
        salt: 盐值（可选）
        
    Returns:
        (hash, salt)
    """
    import secrets
    
    if salt is None:
        salt = secrets.token_hex(32)
    
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000
    ).hex()
    
    return key, salt


def verify_password(password: str, hash: str, salt: str) -> bool:
    """
    验证密码
    
    Args:
        password: 密码
        hash: 哈希值
        salt: 盐值
        
    Returns:
        是否匹配
    """
    new_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(new_hash, hash)


# 导出
__all__ = [
    "generate",
    "generate_strong",
    "generate_weak",
    "check_strength",
    "hash_password",
    "verify_password",
]
