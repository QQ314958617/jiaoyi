"""
Process Utilities - 进程工具
基于 Claude Code process.ts 设计

进程输出处理工具。
"""
import sys
import signal
from typing import Optional


def handle_epipe(stream) -> callable:
    """
    处理EPIPE错误
    
    Args:
        stream: 输出流
        
    Returns:
        错误处理器函数
    """
    def handler(err: Exception):
        if hasattr(err, 'errno') and getattr(err, 'errno', None) == 'EPIPE':
            if hasattr(stream, 'destroy'):
                stream.destroy()
    return handler


def register_process_output_error_handlers() -> None:
    """注册进程输出错误处理器"""
    handle_epipe_stdout = handle_epipe(sys.stdout)
    handle_epipe_stderr = handle_epipe(sys.stderr)
    
    sys.stdout.on = lambda event, handler: None  # 简化
    sys.stderr.on = lambda event, handler: None


def write_to_stdout(data: str) -> None:
    """
    写入stdout
    
    Args:
        data: 数据
    """
    if hasattr(sys.stdout, 'destroyed') and sys.stdout.destroyed:
        return
    sys.stdout.write(data)
    sys.stdout.flush()


def write_to_stderr(data: str) -> None:
    """
    写入stderr
    
    Args:
        data: 数据
    """
    if hasattr(sys.stderr, 'destroyed') and sys.stderr.destroyed:
        return
    sys.stderr.write(data)
    sys.stderr.flush()


def exit_with_error(message: str) -> None:
    """
    输出错误并退出
    
    Args:
        message: 错误消息
    """
    print(message, file=sys.stderr)
    sys.exit(1)


def peek_for_stdin_data(ms: int) -> bool:
    """
    等待stdin数据
    
    Args:
        ms: 超时毫秒数
        
    Returns:
        是否收到数据
    """
    import select
    import sys
    
    if hasattr(sys.stdin, 'closed') and sys.stdin.closed:
        return False
    
    # 使用select检查stdin
    try:
        readable, _, _ = select.select([sys.stdin], [], [], ms / 1000)
        return len(readable) > 0
    except Exception:
        return False


def write_data_to_stream(stream, data: str) -> bool:
    """
    写入数据到流
    
    Args:
        stream: 输出流
        data: 数据
        
    Returns:
        是否成功
    """
    try:
        if hasattr(stream, 'destroyed') and stream.destroyed:
            return False
        stream.write(data)
        return True
    except Exception:
        return False


# 导出
__all__ = [
    "handle_epipe",
    "register_process_output_error_handlers",
    "write_to_stdout",
    "write_to_stderr",
    "exit_with_error",
    "peek_for_stdin_data",
    "write_data_to_stream",
]
