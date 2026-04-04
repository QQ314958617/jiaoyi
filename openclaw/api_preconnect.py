"""
API Preconnect - API预连接
基于 Claude Code apiPreconnect.ts 设计

在初始化期间预连接API，减少首次请求延迟。
"""
import os
import threading
import urllib.request
from typing import Optional


_fired = False
_fired_lock = threading.Lock()


def preconnect_anthropic_api(
    base_url: str = "https://api.anthropic.com",
    timeout_ms: int = 10000,
) -> bool:
    """
    预连接Anthropic API
    
    发起一个HEAD请求来预热TCP+TLS连接。
    
    Args:
        base_url: API基础URL
        timeout_ms: 超时毫秒
        
    Returns:
        是否成功发起
    """
    global _fired
    
    with _fired_lock:
        if _fired:
            return False
        _fired = True
    
    def do_preconnect():
        try:
            req = urllib.request.Request(
                base_url,
                method='HEAD',
            )
            urllib.request.urlopen(req, timeout=timeout_ms / 1000)
        except Exception:
            pass  # 忽略错误
    
    thread = threading.Thread(target=do_preconnect, daemon=True)
    thread.start()
    
    return True


def should_skip_preconnect() -> bool:
    """
    检查是否应该跳过预连接
    
    Returns:
        是否跳过
    """
    # 使用云提供商时跳过
    if os.environ.get('CLAUDE_CODE_USE_BEDROCK'):
        return True
    if os.environ.get('CLAUDE_CODE_USE_VERTEX'):
        return True
    if os.environ.get('CLAUDE_CODE_USE_FOUNDRY'):
        return True
    
    # 使用代理时跳过
    if os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy'):
        return True
    if os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy'):
        return True
    if os.environ.get('ANTHROPIC_UNIX_SOCKET'):
        return True
    if os.environ.get('CLAUDE_CODE_CLIENT_CERT'):
        return True
    if os.environ.get('CLAUDE_CODE_CLIENT_KEY'):
        return True
    
    return False


def reset_preconnect_state() -> None:
    """重置预连接状态（测试用）"""
    global _fired
    with _fired_lock:
        _fired = False


# 导出
__all__ = [
    "preconnect_anthropic_api",
    "should_skip_preconnect",
    "reset_preconnect_state",
]
