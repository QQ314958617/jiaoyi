"""
Request - HTTP请求
基于 Claude Code request.ts 设计

HTTP请求构建工具。
"""
import urllib.request
import urllib.parse
import json
from typing import Dict, Any, Optional


class Request:
    """
    HTTP请求构建器
    """
    
    def __init__(self, url: str):
        """
        Args:
            url: 请求URL
        """
        self._url = url
        self._method = "GET"
        self._headers = {}
        self._body: Optional[Any] = None
        self._timeout = 30
        self._auth: Optional[tuple] = None
    
    def method(self, method: str) -> "Request":
        """设置方法"""
        self._method = method
        return self
    
    def header(self, key: str, value: str) -> "Request":
        """添加请求头"""
        self._headers[key] = value
        return self
    
    def headers(self, headers: Dict[str, str]) -> "Request":
        """批量设置请求头"""
        self._headers.update(headers)
        return self
    
    def body(self, body: Any) -> "Request":
        """设置请求体"""
        self._body = body
        return self
    
    def json(self, data: Any) -> "Request":
        """设置JSON请求体"""
        self._body = json.dumps(data)
        self._headers['Content-Type'] = 'application/json'
        return self
    
    def form(self, data: Dict[str, str]) -> "Request":
        """设置表单请求体"""
        self._body = urllib.parse.urlencode(data)
        self._headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return self
    
    def timeout(self, seconds: int) -> "Request":
        """设置超时"""
        self._timeout = seconds
        return self
    
    def auth(self, username: str, password: str) -> "Request":
        """设置认证"""
        import base64
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self._headers['Authorization'] = f"Basic {encoded}"
        return self
    
    def bearer(self, token: str) -> "Request":
        """Bearer Token认证"""
        self._headers['Authorization'] = f"Bearer {token}"
        return self
    
    def send(self) -> "Response":
        """发送请求"""
        req = urllib.request.Request(self._url, method=self._method)
        
        for key, value in self._headers.items():
            req.add_header(key, value)
        
        if self._body is not None:
            if isinstance(self._body, str):
                self._body = self._body.encode('utf-8')
            req.data = self._body
        
        try:
            import urllib.error
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = resp.read().decode('utf-8')
                return Response(resp.status, body, dict(resp.headers))
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8') if e.fp else ""
            return Response(e.code, body, dict(e.headers) if e.headers else {})
        except Exception as e:
            return Response(0, str(e), {})


class Response:
    """响应对象"""
    
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


def get(url: str) -> Request:
    """创建GET请求"""
    return Request(url)


def post(url: str) -> Request:
    """创建POST请求"""
    return Request(url).method("POST")


def put(url: str) -> Request:
    """创建PUT请求"""
    return Request(url).method("PUT")


def delete(url: str) -> Request:
    """创建DELETE请求"""
    return Request(url).method("DELETE")


def patch(url: str) -> Request:
    """创建PATCH请求"""
    return Request(url).method("PATCH")


# 导出
__all__ = [
    "Request",
    "Response",
    "get",
    "post",
    "put",
    "delete",
    "patch",
]
