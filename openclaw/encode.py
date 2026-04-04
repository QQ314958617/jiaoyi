"""
Encode - 编码
基于 Claude Code encode.ts 设计

编码工具。
"""
import base64
import json
import urllib.parse
from typing import Any, Dict


def json_encode(data: Any) -> str:
    """JSON编码"""
    return json.dumps(data, ensure_ascii=False)


def json_pretty(data: Any, indent: int = 2) -> str:
    """格式化JSON"""
    return json.dumps(data, indent=indent, ensure_ascii=False)


def base64_encode(data: bytes) -> str:
    """Base64编码"""
    return base64.b64encode(data).decode()


def base64_decode(data: str) -> bytes:
    """Base64解码"""
    return base64.b64decode(data)


def base64url_encode(data: bytes) -> str:
    """Base64URL编码"""
    return base64.urlsafe_b64encode(data).decode().rstrip('=')


def base64url_decode(data: str) -> bytes:
    """Base64URL解码"""
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


def url_encode(data: str) -> str:
    """URL编码"""
    return urllib.parse.quote(data)


def url_decode(data: str) -> str:
    """URL解码"""
    return urllib.parse.unquote(data)


def url_encode_params(params: Dict) -> str:
    """URL参数编码"""
    return urllib.parse.urlencode(params)


def url_decode_params(query: str) -> Dict:
    """URL参数解码"""
    return dict(urllib.parse.parse_qsl(query))


def html_encode(data: str) -> str:
    """HTML编码"""
    import html
    return html.escape(data)


def html_decode(data: str) -> str:
    """HTML解码"""
    import html
    return html.unescape(data)


# 导出
__all__ = [
    "json_encode",
    "json_pretty",
    "base64_encode",
    "base64_decode",
    "base64url_encode",
    "base64url_decode",
    "url_encode",
    "url_decode",
    "url_encode_params",
    "url_decode_params",
    "html_encode",
    "html_decode",
]
