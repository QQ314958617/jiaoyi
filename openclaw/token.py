"""
Token - 令牌
基于 Claude Code token.ts 设计

令牌工具。
"""
import secrets
import string


def generate(length: int = 32) -> str:
    """生成随机令牌"""
    return secrets.token_urlsafe(length)


def generate_hex(length: int = 32) -> str:
    """生成十六进制令牌"""
    return secrets.token_hex(length)


def generate_bytes(length: int = 32) -> bytes:
    """生成随机字节"""
    return secrets.token_bytes(length)


def alphanumeric(length: int = 32) -> str:
    """生成字母数字令牌"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def numeric(length: int = 6) -> str:
    """生成数字令牌"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def alphabetic(length: int = 32) -> str:
    """生成纯字母令牌"""
    return ''.join(secrets.choice(string.ascii_letters) for _ in range(length))


def secure_compare(a: str, b: str) -> bool:
    """安全字符串比较（防时序攻击）"""
    return hmac.compare_digest(a, b)


class TokenGenerator:
    """
    令牌生成器
    """
    
    def __init__(self, prefix: str = ""):
        """
        Args:
            prefix: 前缀
        """
        self._prefix = prefix
        self._counter = 0
    
    def next(self, length: int = 32) -> str:
        """生成下一个令牌"""
        token = generate(length)
        return f"{self._prefix}{token}"
    
    def simple(self, length: int = 8) -> str:
        """简短令牌"""
        return f"{self._prefix}{alphanumeric(length)}"
    
    def numeric(self, length: int = 6) -> str:
        """数字令牌"""
        return f"{self._prefix}{numeric(length)}"


# 导出
__all__ = [
    "generate",
    "generate_hex",
    "generate_bytes",
    "alphanumeric",
    "numeric",
    "alphabetic",
    "secure_compare",
    "TokenGenerator",
]
