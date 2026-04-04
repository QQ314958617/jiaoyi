"""
Token - Token工具
基于 Claude Code token.ts 设计

Token生成和解析工具。
"""
import secrets
import time
from typing import Any, Dict, Optional


def generate(length: int = 32) -> str:
    """
    生成随机Token
    
    Args:
        length: 字节长度
        
    Returns:
        十六进制Token
    """
    return secrets.token_hex(length)


def generate_url_safe(length: int = 32) -> str:
    """
    生成URL安全的随机Token
    
    Args:
        length: 字节长度
        
    Returns:
        URL安全Token
    """
    return secrets.token_urlsafe(length)


def generate_numeric(length: int = 6) -> str:
    """
    生成数字Token
    
    Args:
        length: 长度
        
    Returns:
        数字字符串
    """
    result = ''
    for _ in range(length):
        result += secrets.choice('0123456789')
    return result


def generate_alphanumeric(length: int = 32) -> str:
    """
    生成字母数字Token
    
    Args:
        length: 长度
        
    Returns:
        字母数字字符串
    """
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Token:
    """
    Token封装
    
    支持过期和元数据。
    """
    
    def __init__(
        self,
        value: str,
        expires_at: float = None,
        metadata: Dict[str, Any] = None,
    ):
        """
        Args:
            value: Token值
            expires_at: 过期时间戳
            metadata: 元数据
        """
        self.value = value
        self.created_at = time.time()
        self.expires_at = expires_at
        self.metadata = metadata or {}
    
    def is_expired(self) -> bool:
        """是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def ttl(self) -> Optional[float]:
        """剩余生存时间（秒）"""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - time.time()
        return max(0, remaining)


def create_token(
    length: int = 32,
    expires_in: float = None,
    metadata: Dict[str, Any] = None,
) -> Token:
    """
    创建Token
    
    Args:
        length: Token长度
        expires_in: 过期时间（秒）
        metadata: 元数据
        
    Returns:
        Token实例
    """
    value = generate(length)
    expires_at = time.time() + expires_in if expires_in else None
    return Token(value, expires_at, metadata)


class TokenStore:
    """
    Token存储
    
    简单的内存存储。
    """
    
    def __init__(self):
        self._tokens: Dict[str, Token] = {}
        self._by_metadata: Dict[str, str] = {}  # metadata_key -> token_value
    
    def add(self, token: Token) -> None:
        """添加Token"""
        self._tokens[token.value] = token
    
    def get(self, value: str) -> Optional[Token]:
        """获取Token"""
        return self._tokens.get(value)
    
    def validate(self, value: str) -> bool:
        """验证Token"""
        token = self._tokens.get(value)
        if not token:
            return False
        if token.is_expired():
            self.remove(value)
            return False
        return True
    
    def remove(self, value: str) -> bool:
        """删除Token"""
        if value in self._tokens:
            del self._tokens[value]
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """清理过期Token"""
        expired = [
            value for value, token in self._tokens.items()
            if token.is_expired()
        ]
        for value in expired:
            del self._tokens[value]
        return len(expired)


# 导出
__all__ = [
    "generate",
    "generate_url_safe",
    "generate_numeric",
    "generate_alphanumeric",
    "Token",
    "create_token",
    "TokenStore",
]
