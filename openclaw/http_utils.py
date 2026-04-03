"""
OpenClaw HTTP Utilities
===================
Inspired by Claude Code's src/utils/http.ts.

HTTP 工具，支持：
1. User-Agent 生成
2. 请求头构建
3. 常见状态码
4. HTTP 错误类
"""

from __future__ import annotations

import os, platform
from dataclasses import dataclass
from typing import Optional, Dict, Any

# ============================================================================
# 版本信息
# ============================================================================

VERSION = "1.0.0"
SDK_VERSION = os.environ.get("CLAUDE_AGENT_SDK_VERSION", "")
CLIENT_APP = os.environ.get("CLAUDE_AGENT_SDK_CLIENT_APP", "")

# ============================================================================
# User-Agent
# ============================================================================

def get_user_agent() -> str:
    """
    获取 User-Agent 字符串
    
    Returns:
        User-Agent 字符串
    """
    parts = []
    
    if SDK_VERSION:
        parts.append(f"agent-sdk/{SDK_VERSION}")
    
    if CLIENT_APP:
        parts.append(f"client-app/{CLIENT_APP}")
    
    suffix = ""
    if parts:
        suffix = f" ({', '.join(parts)})"
    
    system = platform.system()
    version = platform.version()
    
    return f"OpenClaw/{VERSION} ({system}, {version}){suffix}"

def get_mcp_user_agent() -> str:
    """
    获取 MCP User-Agent
    
    用于 MCP 服务器通信
    """
    parts = []
    
    if SDK_VERSION:
        parts.append(f"agent-sdk/{SDK_VERSION}")
    
    if CLIENT_APP:
        parts.append(f"client-app/{CLIENT_APP}")
    
    suffix = ""
    if parts:
        suffix = f" ({', '.join(parts)})"
    
    return f"openclaw-mcp/{VERSION}{suffix}"

def get_web_fetch_user_agent() -> str:
    """
    获取 WebFetch User-Agent
    
    用于抓取网页
    """
    return f"Claude-User ({get_user_agent()}; +https://support.anthropic.com/)"

# ============================================================================
# HTTP 状态码
# ============================================================================

class HTTPStatus:
    """HTTP 状态码常量"""
    # 1xx 信息
    CONTINUE = 100
    SWITCHING_PROTOCOLS = 101
    PROCESSING = 102
    
    # 2xx 成功
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    PARTIAL_CONTENT = 206
    
    # 3xx 重定向
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308
    
    # 4xx 客户端错误
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    PAYLOAD_TOO_LARGE = 413
    URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    RANGE_NOT_SATISFIABLE = 416
    EXPECTATION_FAILED = 417
    TEAPOT = 418  # I'm a teapot (April Fools')
    
    # 5xx 服务器错误
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505

def is_success(status: int) -> bool:
    """是否是成功状态码（2xx）"""
    return 200 <= status < 300

def is_redirect(status: int) -> bool:
    """是否是重定向状态码（3xx）"""
    return 300 <= status < 400

def is_client_error(status: int) -> bool:
    """是否是客户端错误（4xx）"""
    return 400 <= status < 500

def is_server_error(status: int) -> bool:
    """是否是服务器错误（5xx）"""
    return 500 <= status < 600

def status_text(status: int) -> str:
    """获取状态码的文本描述"""
    texts = {
        200: "OK",
        201: "Created",
        204: "No Content",
        301: "Moved Permanently",
        302: "Found",
        304: "Not Modified",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        408: "Request Timeout",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }
    return texts.get(status, "Unknown")

# ============================================================================
# HTTP 错误
# ============================================================================

class HTTPError(Exception):
    """HTTP 错误基类"""
    def __init__(self, message: str, status: int = 0, response: Any = None):
        self.message = message
        self.status = status
        self.response = response
        super().__init__(message)

class BadRequestError(HTTPError):
    """400 Bad Request"""
    def __init__(self, message: str = "Bad Request"):
        super().__init__(message, 400)

class UnauthorizedError(HTTPError):
    """401 Unauthorized"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, 401)

class ForbiddenError(HTTPError):
    """403 Forbidden"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)

class NotFoundError(HTTPError):
    """404 Not Found"""
    def __init__(self, message: str = "Not Found"):
        super().__init__(message, 404)

class RateLimitError(HTTPError):
    """429 Too Many Requests"""
    def __init__(self, message: str = "Too Many Requests", retry_after: Optional[float] = None):
        self.retry_after = retry_after
        super().__init__(message, 429)

class ServerError(HTTPError):
    """5xx 服务器错误"""
    def __init__(self, message: str = "Internal Server Error", status: int = 500):
        super().__init__(message, status)

# ============================================================================
# 响应封装
# ============================================================================

@dataclass
class HTTPResponse:
    """HTTP 响应封装"""
    status: int
    headers: Dict[str, str]
    content: Any
    text: Optional[str] = None
    json: Optional[Any] = None
    error: Optional[str] = None
    
    @property
    def ok(self) -> bool:
        return is_success(self.status)
    
    @property
    def is_json(self) -> bool:
        return self.json is not None

# ============================================================================
# 请求头构建
# ============================================================================

def build_headers(extra: Optional[Dict[str, str]] = None,
                 auth: Optional[str] = None,
                 content_type: Optional[str] = None) -> Dict[str, str]:
    """
    构建 HTTP 请求头
    
    Args:
        extra: 额外的请求头
        auth: Authorization 头值
        content_type: Content-Type 头值
    
    Returns:
        请求头字典
    """
    headers = {
        "User-Agent": get_user_agent(),
        "Accept": "application/json, text/plain, */*",
    }
    
    if auth:
        headers["Authorization"] = auth
    
    if content_type:
        headers["Content-Type"] = content_type
    
    if extra:
        headers.update(extra)
    
    return headers

def build_json_headers(auth: Optional[str] = None) -> Dict[str, str]:
    """构建 JSON 请求头"""
    return build_headers(auth=auth, content_type="application/json")

# ============================================================================
# 便捷请求方法
# ============================================================================

import aiohttp

async def get(url: str, params: Optional[Dict] = None,
             headers: Optional[Dict[str, str]] = None,
             timeout: float = 30.0) -> HTTPResponse:
    """
    发送 GET 请求
    """
    if headers is None:
        headers = build_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers,
                                 timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                text = await resp.text()
                json_data = None
                try:
                    json_data = await resp.json()
                except:
                    pass
                
                return HTTPResponse(
                    status=resp.status,
                    headers=dict(resp.headers),
                    content=text,
                    text=text,
                    json=json_data
                )
    except aiohttp.ClientError as e:
        return HTTPResponse(
            status=0,
            headers={},
            content="",
            error=str(e)
        )

async def post(url: str, data: Any = None,
              json_data: Any = None,
              headers: Optional[Dict[str, str]] = None,
              timeout: float = 30.0) -> HTTPResponse:
    """
    发送 POST 请求
    """
    if headers is None:
        headers = build_json_headers()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, json=json_data,
                                 headers=headers,
                                 timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                text = await resp.text()
                json_data = None
                try:
                    json_data = await resp.json()
                except:
                    pass
                
                return HTTPResponse(
                    status=resp.status,
                    headers=dict(resp.headers),
                    content=text,
                    text=text,
                    json=json_data
                )
    except aiohttp.ClientError as e:
        return HTTPResponse(
            status=0,
            headers={},
            content="",
            error=str(e)
        )
