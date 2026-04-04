"""
OTP - 一次性密码
基于 Claude Code otp.ts 设计

OTP工具。
"""
import hmac
import base64
import struct
import time
import hashlib


def HOTP(secret: str, counter: int, digits: int = 6) -> str:
    """
    HOTP (HMAC-based OTP)
    
    Args:
        secret: 共享密钥(base64)
        counter: 计数器
        digits: 验证码位数
        
    Returns:
        验证码
    """
    secret_bytes = base64.b32decode(secret.upper() + '=' * (8 - len(secret) % 8))
    counter_bytes = struct.pack('>Q', counter)
    
    mac = hmac.new(secret_bytes, counter_bytes, hashlib.sha1).digest()
    offset = mac[-1] & 0x0f
    binary = struct.unpack('>I', mac[offset:offset+4])[0] & 0x7fffffff
    
    otp = str(binary % (10 ** digits))
    return otp.zfill(digits)


def TOTP(secret: str, period: int = 30, digits: int = 6, timestamp: int = None) -> str:
    """
    TOTP (Time-based OTP)
    
    Args:
        secret: 共享密钥
        period: 时间周期（秒）
        digits: 验证码位数
        timestamp: 时间戳（默认当前）
        
    Returns:
        验证码
    """
    if timestamp is None:
        timestamp = int(time.time())
    
    counter = timestamp // period
    return HOTP(secret, counter, digits)


def generate_secret(length: int = 20) -> str:
    """
    生成随机密钥
    
    Args:
        length: 长度
        
    Returns:
        Base32编码的密钥
    """
    import secrets
    secret_bytes = secrets.token_bytes(length)
    return base64.b32encode(secret_bytes).decode().rstrip('=')


def verify(otp: str, secret: str, period: int = 30, window: int = 1) -> bool:
    """
    验证OTP
    
    Args:
        otp: 用户输入的验证码
        secret: 共享密钥
        period: 时间周期
        window: 允许的时间窗口（前后各几个周期）
        
    Returns:
        是否有效
    """
    current_time = int(time.time())
    
    for offset in range(-window, window + 1):
        counter = (current_time // period) + offset
        expected = HOTP(secret, counter)
        if hmac.compare_digest(otp, expected):
            return True
    
    return False


# 导出
__all__ = [
    "HOTP",
    "TOTP",
    "generate_secret",
    "verify",
]
