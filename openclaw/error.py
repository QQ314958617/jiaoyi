"""
Error - 错误工具
基于 Claude Code error.ts 设计

错误处理工具。
"""
import traceback
from typing import Any, Optional


class AppError(Exception):
    """
    应用错误基类
    
    支持错误码和附加数据。
    """
    
    def __init__(
        self,
        message: str,
        code: str = None,
        data: dict = None,
        cause: Exception = None,
    ):
        """
        Args:
            message: 错误消息
            code: 错误码
            data: 附加数据
            cause: 原始异常
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data or {}
        self.cause = cause
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"[{self.code}]")
        return ' '.join(parts)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "message": self.message,
            "code": self.code,
            "data": self.data,
        }


class NotFoundError(AppError):
    """资源未找到错误"""
    
    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message, code="NOT_FOUND", **kwargs)


class ValidationAppError(AppError):
    """验证错误"""
    
    def __init__(self, message: str = "Validation error", **kwargs):
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)


class UnauthorizedError(AppError):
    """未授权错误"""
    
    def __init__(self, message: str = "Unauthorized", **kwargs):
        super().__init__(message, code="UNAUTHORIZED", **kwargs)


class ForbiddenError(AppError):
    """禁止错误"""
    
    def __init__(self, message: str = "Forbidden", **kwargs):
        super().__init__(message, code="FORBIDDEN", **kwargs)


class ConflictError(AppError):
    """冲突错误"""
    
    def __init__(self, message: str = "Conflict", **kwargs):
        super().__init__(message, code="CONFLICT", **kwargs)


def get_error_message(error: Exception) -> str:
    """获取错误消息"""
    if isinstance(error, AppError):
        return error.message
    return str(error)


def get_error_code(error: Exception) -> Optional[str]:
    """获取错误码"""
    if isinstance(error, AppError):
        return error.code
    return None


def get_error_stack(error: Exception) -> str:
    """获取堆栈跟踪"""
    return traceback.format_exc()


def format_error(error: Exception, include_stack: bool = False) -> str:
    """
    格式化错误
    
    Args:
        error: 异常
        include_stack: 是否包含堆栈
        
    Returns:
        格式化的错误字符串
    """
    parts = []
    
    if isinstance(error, AppError):
        parts.append(f"[{error.code}] {error.message}" if error.code else error.message)
    else:
        parts.append(str(error))
    
    if include_stack:
        parts.append(get_error_stack(error))
    
    return '\n'.join(parts)


def is_error_type(error: Exception, error_class: type) -> bool:
    """检查错误类型"""
    return isinstance(error, error_class)


def catch_async(func):
    """异步函数异常捕获装饰器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AppError:
            raise
        except Exception as e:
            raise AppError(str(e), cause=e)
    return wrapper


# 导出
__all__ = [
    "AppError",
    "NotFoundError",
    "ValidationAppError",
    "UnauthorizedError",
    "ForbiddenError",
    "ConflictError",
    "get_error_message",
    "get_error_code",
    "get_error_stack",
    "format_error",
    "is_error_type",
    "catch_async",
]
