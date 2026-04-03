"""
OpenClaw Error Utilities
========================
Inspired by Claude Code's src/utils/errors.ts (238 lines).

统一错误处理工具，支持：
1. 错误类型分类
2. 错误消息提取
3. errno 代码提取
4. 错误堆栈裁剪
5. 错误规范化
"""

from __future__ import annotations

import asyncio, traceback, sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any

# ============================================================================
# 错误类型
# ============================================================================

class ErrnoCode(Enum):
    ENOENT = "ENOENT"
    EACCES = "EACCES"
    EPERM = "EPERM"
    ENOTDIR = "ENOTDIR"
    ELOOP = "ELOOP"
    ECONNRESET = "ECONNRESET"
    ETIMEDOUT = "ETIMEDOUT"
    ECONNREFUSED = "ECONNREFUSED"
    ENOTFOUND = "ENOTFOUND"
    EHOSTUNREACH = "EHOSTUNREACH"

class HTTPErrorKind(Enum):
    AUTH = "auth"
    TIMEOUT = "timeout"
    NETWORK = "network"
    HTTP = "http"
    OTHER = "other"

# ============================================================================
# 异常类
# ============================================================================

class OpenClawError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

class AbortError(OpenClawError):
    def __init__(self, message: str = "Aborted"):
        super().__init__(message)

class ConfigParseError(OpenClawError):
    def __init__(self, message: str, file_path: str = ""):
        super().__init__(message)
        self.file_path = file_path

class ShellError(OpenClawError):
    def __init__(self, message: str, stdout: str = "", stderr: str = "", code: int = 1):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.code = code

class NetworkError(OpenClawError):
    def __init__(self, message: str, kind: HTTPErrorKind = HTTPErrorKind.OTHER):
        super().__init__(message)
        self.kind = kind

class APIError(OpenClawError):
    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status

class ValidationError(OpenClawError):
    def __init__(self, message: str):
        super().__init__(message)

# ============================================================================
# 错误检查函数
# ============================================================================

def is_abort_error(e: BaseException) -> bool:
    if isinstance(e, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)):
        return True
    if isinstance(e, AbortError):
        return True
    if hasattr(e, '__class__') and e.__class__.__name__ in ('KeyboardInterrupt', 'SystemExit'):
        return True
    return False

def get_errno_code(e: BaseException) -> Optional[str]:
    if hasattr(e, 'errno') and isinstance(e.errno, int):
        import errno as _errno
        for name in dir(_errno):
            if name.startswith('E') and getattr(_errno, name) == e.errno:
                return name
        return str(e.errno)
    if hasattr(e, 'code') and isinstance(e.code, str):
        return e.code
    return None

def is_enoent(e: BaseException) -> bool:
    return get_errno_code(e) == 'ENOENT'

def is_eacces(e: BaseException) -> bool:
    return get_errno_code(e) == 'EACCES'

def is_fs_inaccessible(e: BaseException) -> bool:
    code = get_errno_code(e)
    return code in ('ENOENT', 'EACCES', 'EPERM', 'ENOTDIR', 'ELOOP')

def is_network_error(e: BaseException) -> bool:
    code = get_errno_code(e)
    return code in ('ECONNRESET', 'ETIMEDOUT', 'ECONNREFUSED', 'ENOTFOUND', 'EHOSTUNREACH')

# ============================================================================
# 错误消息处理
# ============================================================================

def error_message(e: BaseException) -> str:
    if isinstance(e, Exception):
        return str(e)
    return repr(e)

def to_error(e: Any) -> BaseException:
    if isinstance(e, BaseException):
        return e
    return Exception(str(e))

def short_error_stack(e: BaseException, max_frames: int = 5) -> str:
    if not isinstance(e, Exception):
        return str(e)
    stack = traceback.format_exception(type(e), e, e.__traceback__)
    stack_str = ''.join(stack)
    if stack_str.count('\n') <= max_frames + 2:
        return stack_str
    lines = stack_str.split('\n')
    header_lines = []
    frame_lines = []
    in_frames = False
    for line in lines:
        if line.startswith('  '):
            in_frames = True
        if in_frames:
            if line.strip().startswith('File ') or line.strip().startswith('  '):
                frame_lines.append(line)
        else:
            header_lines.append(line)
    frames = frame_lines[:max_frames]
    return '\n'.join(header_lines + frames)

# ============================================================================
# HTTP 错误分类
# ============================================================================

@dataclass
class HTTPErrorInfo:
    kind: HTTPErrorKind
    status: Optional[int]
    message: str

def classify_axios_error(e: BaseException) -> HTTPErrorInfo:
    message = error_message(e)
    if hasattr(e, 'response') and isinstance(e.response, dict):
        status = e.response.get('status')
        if status in (401, 403):
            return HTTPErrorInfo(HTTPErrorKind.AUTH, status, message)
    code = get_errno_code(e)
    if code in ('ECONNABORTED', 'ETIMEDOUT'):
        return HTTPErrorInfo(HTTPErrorKind.TIMEOUT, None, message)
    if code in ('ECONNREFUSED', 'ENOTFOUND', 'EHOSTUNREACH', 'ECONNRESET'):
        return HTTPErrorInfo(HTTPErrorKind.NETWORK, None, message)
    if hasattr(e, 'status') and isinstance(e.status, int):
        return HTTPErrorInfo(HTTPErrorKind.HTTP, e.status, message)
    return HTTPErrorInfo(HTTPErrorKind.OTHER, None, message)

def wrap_network_error(e: BaseException, context: str = "") -> NetworkError:
    info = classify_axios_error(e)
    msg = f"{context}: {info.message}" if context else info.message
    return NetworkError(msg, info.kind)

def wrap_api_error(e: BaseException, context: str = "") -> APIError:
    message = error_message(e)
    status = None
    if hasattr(e, 'response') and isinstance(e.response, dict):
        status = e.response.get('status')
    msg = f"{context}: {message}" if context else message
    return APIError(msg, status)
