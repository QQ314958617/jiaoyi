"""
Encoding - 编码
基于 Claude Code encoding.ts 设计

编码工具。
"""
import base64
import json
from typing import Any


def to_base64(data: bytes) -> str:
    """Base64编码"""
    return base64.b64encode(data).decode()


def from_base64(data: str) -> bytes:
    """Base64解码"""
    return base64.b64decode(data)


def to_base64url(data: bytes) -> str:
    """Base64URL编码"""
    return base64.urlsafe_b64encode(data).decode().rstrip('=')


def from_base64url(data: str) -> bytes:
    """Base64URL解码"""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def to_hex(data: bytes) -> str:
    """十六进制编码"""
    return data.hex()


def from_hex(data: str) -> bytes:
    """十六进制解码"""
    return bytes.fromhex(data)


def to_json(obj: Any) -> str:
    """JSON编码"""
    return json.dumps(obj, ensure_ascii=False)


def from_json(data: str) -> Any:
    """JSON解码"""
    return json.loads(data)


def compress_gzip(data: bytes) -> bytes:
    """GZIP压缩"""
    import gzip
    return gzip.compress(data)


def decompress_gzip(data: bytes) -> bytes:
    """GZIP解压"""
    import gzip
    return gzip.decompress(data)


# 导出
__all__ = [
    "to_base64",
    "from_base64",
    "to_base64url",
    "from_base64url",
    "to_hex",
    "from_hex",
    "to_json",
    "from_json",
    "compress_gzip",
    "decompress_gzip",
]
