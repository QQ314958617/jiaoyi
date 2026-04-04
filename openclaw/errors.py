"""
Errors - 错误类定义
基于 Claude Code errors.ts 设计

定义各种错误类型。
"""
from typing import Optional


class ClaudeError(Exception):
    """基础Claude错误"""
    def __init__(self, message: str):
        super().__init__(message)
        self.name = self.__class__.__name__


class MalformedCommandError(ClaudeError):
    """命令格式错误"""
    pass


class AbortError(ClaudeError):
    """中断错误"""
    def __init__(self, message: str = ""):
        super().__init__(message)
        self.name = "AbortError"


def is_abort_error(e: Exception) -> bool:
    """
    判断是否为中断错误
    
    Args:
        e: 异常
        
    Returns:
        是否为中断错误
    """
    return (
        isinstance(e, AbortError) or
        (isinstance(e, Exception) and e.name == "AbortError")
    )


class ConfigParseError(ClaudeError):
    """配置文件解析错误"""
    
    def __init__(
        self,
        message: str,
        file_path: str,
        default_config: Optional[dict] = None,
    ):
        super().__init__(message)
        self.name = "ConfigParseError"
        self.file_path = file_path
        self.default_config = default_config


class ShellError(ClaudeError):
    """Shell命令错误"""
    
    def __init__(
        self,
        stdout: str,
        stderr: str,
        code: int,
        interrupted: bool = False,
    ):
        super().__init__("Shell command failed")
        self.name = "ShellError"
        self.stdout = stdout
        self.stderr = stderr
        self.code = code
        self.interrupted = interrupted


class TelportOperationError(ClaudeError):
    """远程操作错误"""
    
    def __init__(self, message: str, formatted_message: str = ""):
        super().__init__(message)
        self.name = "TeleportOperationError"
        self.formatted_message = formatted_message or message


class TelemetrySafeError(ClaudeError):
    """
    可安全记录到遥测的错误
    
    验证错误消息不包含敏感数据。
    """
    
    def __init__(
        self,
        message: str,
        telemetry_message: Optional[str] = None,
    ):
        super().__init__(message)
        self.name = "TelemetrySafeError"
        self.telemetry_message = telemetry_message or message


class APIError(ClaudeError):
    """API错误"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[dict] = None,
    ):
        super().__init__(message)
        self.name = "APIError"
        self.status_code = status_code
        self.response = response


class ToolError(ClaudeError):
    """工具执行错误"""
    pass


class PermissionError(ClaudeError):
    """权限错误"""
    pass


# 错误日志
_error_log: list[dict] = []


def log_error(error: Exception | str) -> None:
    """
    记录错误
    
    Args:
        error: 异常或错误字符串
    """
    import traceback
    from datetime import datetime, timezone
    
    if isinstance(error, str):
        _error_log.append({
            "error": error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "string",
        })
    else:
        _error_log.append({
            "error": str(error),
            "type": type(error).__name__,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


def get_error_log(limit: int = 100) -> list[dict]:
    """
    获取错误日志
    
    Args:
        limit: 返回数量限制
        
    Returns:
        错误日志列表
    """
    return _error_log[-limit:]


def clear_error_log() -> None:
    """清空错误日志"""
    _error_log.clear()


# 导出
__all__ = [
    "ClaudeError",
    "MalformedCommandError",
    "AbortError",
    "is_abort_error",
    "ConfigParseError",
    "ShellError",
    "TeleportOperationError",
    "TelemetrySafeError",
    "APIError",
    "ToolError",
    "PermissionError",
    "log_error",
    "get_error_log",
    "clear_error_log",
]
