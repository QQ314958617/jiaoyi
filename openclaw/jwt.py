"""
JWT - JSON Web Token
基于 Claude Code jwt.ts 设计

简化的JWT工具。
"""
import base64
import json
import time
from typing import Any, Dict, Optional


def _base64_encode(data: dict) -> str:
    """Base64 URL编码"""
    json_str = json.dumps(data, separators=(',', ':'))
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    return encoded.rstrip('=')


def _base64_decode(data: str) -> dict:
    """Base64 URL解码"""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    json_str = base64.urlsafe_b64decode(data.encode()).decode()
    return json.loads(json_str)


class JWT:
    """
    JSON Web Token
    
    简化实现，仅支持HS256。
    """
    
    def __init__(self, secret: str):
        """
        Args:
            secret: 密钥
        """
        self._secret = secret
        self._algorithm = 'HS256'
    
    def encode(
        self,
        payload: Dict[str, Any],
        expires_in: int = None,
    ) -> str:
        """
        编码Token
        
        Args:
            payload: 载荷
            expires_in: 过期时间（秒）
            
        Returns:
            JWT字符串
        """
        import hmac
        import hashlib
        
        # 添加标准声明
        if expires_in:
            payload['exp'] = int(time.time()) + expires_in
        
        payload['iat'] = int(time.time())
        
        # Header
        header = {'alg': self._algorithm, 'typ': 'JWT'}
        header_encoded = _base64_encode(header)
        
        # Payload
        payload_encoded = _base64_encode(payload)
        
        # Signature
        message = f"{header_encoded}.{payload_encoded}"
        signature = hmac.new(
            self._secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{message}.{signature}"
    
    def decode(self, token: str, verify: bool = True) -> Optional[Dict[str, Any]]:
        """
        解码Token
        
        Args:
            token: JWT字符串
            verify: 是否验证签名
            
        Returns:
            载荷或None
        """
        import hmac
        import hashlib
        
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_encoded, payload_encoded, signature = parts
            
            # 验证签名
            if verify:
                message = f"{header_encoded}.{payload_encoded}"
                expected = hmac.new(
                    self._secret.encode(),
                    message.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                if signature != expected:
                    return None
            
            # 解码payload
            payload = _base64_decode(payload_encoded)
            
            # 验证过期
            if verify and 'exp' in payload:
                if time.time() > payload['exp']:
                    return None
            
            return payload
        
        except Exception:
            return None
    
    def verify(self, token: str) -> bool:
        """验证Token"""
        return self.decode(token, verify=True) is not None


def create_jwt(
    secret: str,
    payload: Dict[str, Any],
    expires_in: int = None,
) -> str:
    """
    创建JWT
    
    Args:
        secret: 密钥
        payload: 载荷
        expires_in: 过期时间（秒）
        
    Returns:
        JWT字符串
    """
    jwt = JWT(secret)
    return jwt.encode(payload, expires_in)


def decode_jwt(
    secret: str,
    token: str,
    verify: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    解码JWT
    
    Args:
        secret: 密钥
        token: JWT字符串
        verify: 是否验证
        
    Returns:
        载荷或None
    """
    jwt = JWT(secret)
    return jwt.decode(token, verify)


# 导出
__all__ = [
    "JWT",
    "create_jwt",
    "decode_jwt",
]
