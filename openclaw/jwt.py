"""
JWT - JSON Web Token
基于 Claude Code jwt.ts 设计

JWT工具。
"""
import base64
import json
import time
from typing import Dict, Optional


class JWT:
    """
    JWT工具
    """
    
    def __init__(self, secret: str = ""):
        """
        Args:
            secret: 密钥
        """
        self._secret = secret
    
    def encode(self, payload: Dict, expires_in: int = 3600) -> str:
        """
        编码JWT
        
        Args:
            payload: 数据载荷
            expires_in: 过期时间（秒）
            
        Returns:
            JWT字符串
        """
        # 添加过期时间
        payload = dict(payload)
        payload['exp'] = int(time.time()) + expires_in
        payload['iat'] = int(time.time())
        
        # Header
        header = {'alg': 'HS256', 'typ': 'JWT'}
        
        # Base64编码
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip('=')
        
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=')
        
        # 签名
        import hmac
        import hashlib
        
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(
            self._secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        return f"{message}.{signature_b64}"
    
    def decode(self, token: str) -> Optional[Dict]:
        """
        解码JWT
        
        Args:
            token: JWT字符串
            
        Returns:
            载荷或None（验证失败）
        """
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_b64, payload_b64, signature_b64 = parts
            
            # 验证签名
            import hmac
            import hashlib
            
            message = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(
                self._secret.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')
            
            if not hmac.compare_digest(signature_b64, expected_sig_b64):
                return None
            
            # 解析payload
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            
            payload = json.loads(
                base64.urlsafe_b64decode(payload_b64.encode()).decode()
            )
            
            # 检查过期
            if 'exp' in payload and payload['exp'] < time.time():
                return None
            
            return payload
            
        except Exception:
            return None
    
    def verify(self, token: str) -> bool:
        """验证JWT"""
        return self.decode(token) is not None


def create_token(payload: Dict, secret: str, expires_in: int = 3600) -> str:
    """
    创建JWT（便捷函数）
    
    Args:
        payload: 数据载荷
        secret: 密钥
        expires_in: 过期时间（秒）
        
    Returns:
        JWT字符串
    """
    jwt = JWT(secret)
    return jwt.encode(payload, expires_in)


def verify_token(token: str, secret: str) -> Optional[Dict]:
    """
    验证JWT（便捷函数）
    
    Args:
        token: JWT字符串
        secret: 密钥
        
    Returns:
        载荷或None
    """
    jwt = JWT(secret)
    return jwt.decode(token)


# 导出
__all__ = [
    "JWT",
    "create_token",
    "verify_token",
]
