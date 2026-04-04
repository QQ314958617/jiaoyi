"""
Fetch - HTTP获取
基于 Claude Code fetch.ts 设计

Fetch API风格的HTTP工具。
"""
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Dict, Any, Optional


class Response:
    """模拟Fetch Response"""
    
    def __init__(self, status: int, body: str, headers: Dict[str, str]):
        self.status = status
        self.ok = 200 <= status < 300
        self.body = body
        self.headers = headers
        self._json = None
    
    def json(self) -> Any:
        """解析JSON"""
        if self._json is None:
            self._json = json.loads(self.body)
        return self._json
    
    def text(self) -> str:
        """获取文本"""
        return self.body


async def fetch(url: str, method: str = "GET", 
               headers: Dict[str, str] = None,
               body: Any = None,
               timeout: int = 30) -> Response:
    """
    Fetch风格的HTTP请求
    
    Args:
        url: URL
        method: HTTP方法
        headers: 请求头
        body: 请求体
        timeout: 超时
        
    Returns:
        Response对象
    """
    req = urllib.request.Request(url, method=method)
    
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    
    if body is not None:
        if isinstance(body, dict):
            body = json.dumps(body).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        elif isinstance(body, str):
            body = body.encode('utf-8')
        if isinstance(body, bytes):
            req.data = body
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8')
            return Response(
                status=resp.status,
                body=body,
                headers=dict(resp.headers)
            )
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8') if e.fp else ""
        return Response(
            status=e.code,
            body=body,
            headers=dict(e.headers) if e.headers else {}
        )
    except Exception as e:
        return Response(
            status=0,
            body=str(e),
            headers={}
        )


def get(url: str, headers: Dict[str, str] = None, timeout: int = 30) -> Response:
    """GET请求"""
    return fetch(url, "GET", headers, None, timeout)


def post(url: str, body: Any = None, headers: Dict[str, str] = None, 
         timeout: int = 30) -> Response:
    """POST请求"""
    return fetch(url, "POST", headers, body, timeout)


def put(url: str, body: Any = None, headers: Dict[str, str] = None,
        timeout: int = 30) -> Response:
    """PUT请求"""
    return fetch(url, "PUT", headers, body, timeout)


def delete(url: str, headers: Dict[str, str] = None, timeout: int = 30) -> Response:
    """DELETE请求"""
    return fetch(url, "DELETE", headers, None, timeout)


# 导出
__all__ = [
    "Response",
    "fetch",
    "get",
    "post",
    "put",
    "delete",
]
