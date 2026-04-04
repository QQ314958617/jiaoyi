"""
HTTP - HTTP请求
基于 Claude Code http.ts 设计

HTTP工具。
"""
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Dict, Any, Optional


def get(url: str, headers: Dict[str, str] = None, timeout: int = 30) -> dict:
    """
    GET请求
    
    Returns:
        {"status": 200, "body": "", "headers": {}}
    """
    req = urllib.request.Request(url)
    
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8')
            return {
                "status": resp.status,
                "body": body,
                "headers": dict(resp.headers)
            }
    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "body": e.read().decode('utf-8') if e.fp else "",
            "headers": dict(e.headers) if e.headers else {}
        }
    except Exception as e:
        return {
            "status": 0,
            "body": str(e),
            "headers": {}
        }


def post(url: str, data: Any = None, headers: Dict[str, str] = None, 
         timeout: int = 30) -> dict:
    """
    POST请求
    
    Args:
        data: body数据（dict会转为json，str直接发送）
    """
    req = urllib.request.Request(url, method='POST')
    
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    
    if data is not None:
        if isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        elif isinstance(data, str):
            data = data.encode('utf-8')
        req.data = data
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8')
            return {
                "status": resp.status,
                "body": body,
                "headers": dict(resp.headers)
            }
    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "body": e.read().decode('utf-8') if e.fp else "",
            "headers": dict(e.headers) if e.headers else {}
        }
    except Exception as e:
        return {
            "status": 0,
            "body": str(e),
            "headers": {}
        }


def put(url: str, data: Any = None, headers: Dict[str, str] = None,
        timeout: int = 30) -> dict:
    """PUT请求"""
    req = urllib.request.Request(url, method='PUT')
    
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    
    if data is not None:
        if isinstance(data, dict):
            data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        elif isinstance(data, str):
            data = data.encode('utf-8')
        req.data = data
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8')
            return {
                "status": resp.status,
                "body": body,
                "headers": dict(resp.headers)
            }
    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "body": e.read().decode('utf-8') if e.fp else "",
            "headers": dict(e.headers) if e.headers else {}
        }
    except Exception as e:
        return {
            "status": 0,
            "body": str(e),
            "headers": {}
        }


def delete(url: str, headers: Dict[str, str] = None, timeout: int = 30) -> dict:
    """DELETE请求"""
    req = urllib.request.Request(url, method='DELETE')
    
    if headers:
        for key, value in headers.items():
            req.add_header(key, value)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8')
            return {
                "status": resp.status,
                "body": body,
                "headers": dict(resp.headers)
            }
    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "body": e.read().decode('utf-8') if e.fp else "",
            "headers": dict(e.headers) if e.headers else {}
        }
    except Exception as e:
        return {
            "status": 0,
            "body": str(e),
            "headers": {}
        }


def json_get(url: str, headers: Dict[str, str] = None, timeout: int = 30) -> Any:
    """GET JSON"""
    result = get(url, headers, timeout)
    if result["status"] == 200:
        try:
            return json.loads(result["body"])
        except json.JSONDecodeError:
            return None
    return None


def json_post(url: str, data: Any = None, headers: Dict[str, str] = None,
              timeout: int = 30) -> Any:
    """POST JSON"""
    result = post(url, data, headers, timeout)
    if result["status"] == 200:
        try:
            return json.loads(result["body"])
        except json.JSONDecodeError:
            return None
    return None


# 导出
__all__ = [
    "get",
    "post",
    "put",
    "delete",
    "json_get",
    "json_post",
]
