"""
URI - URI工具
基于 Claude Code uri.ts 设计

URI解析和操作工具。
"""
import urllib.parse
from typing import Any, Dict, Optional


class URI:
    """
    URI
    
    解析和操作URI。
    """
    
    def __init__(self, uri: str):
        """
        Args:
            uri: URI字符串
        """
        self._uri = uri
        self._parsed = urllib.parse.urlparse(uri)
    
    @property
    def scheme(self) -> str:
        """协议"""
        return self._parsed.scheme
    
    @property
    def username(self) -> str:
        """用户名"""
        return self._parsed.username or ''
    
    @property
    def password(self) -> str:
        """密码"""
        return self._parsed.password or ''
    
    @property
    def host(self) -> str:
        """主机"""
        return self._parsed.hostname or ''
    
    @property
    def port(self) -> Optional[int]:
        """端口"""
        return self._parsed.port
    
    @property
    def path(self) -> str:
        """路径"""
        return self._parsed.path
    
    @property
    def query(self) -> Dict[str, str]:
        """查询参数"""
        return dict(urllib.parse.parse_qsl(self._parsed.query))
    
    @property
    def fragment(self) -> str:
        """片段"""
        return self._parsed.fragment
    
    @property
    def origin(self) -> str:
        """源（scheme://host[:port]）"""
        result = f"{self.scheme}://{self.host}"
        if self.port:
            result += f":{self.port}"
        return result
    
    @property
    def authority(self) -> str:
        """权限（[user:pass@]host[:port]）"""
        result = ''
        if self.username:
            result += self.username
            if self.password:
                result += f":{self.password}"
            result += '@'
        
        result += self.host
        
        if self.port:
            result += f":{self.port}"
        
        return result
    
    def get_param(self, key: str, default: str = None) -> str:
        """获取查询参数"""
        return self.query.get(key, default)
    
    def with_scheme(self, scheme: str) -> "URI":
        """设置协议"""
        return URI(self._update(scheme=scheme))
    
    def with_host(self, host: str) -> "URI":
        """设置主机"""
        return URI(self._update(host=host))
    
    def with_port(self, port: int) -> "URI":
        """设置端口"""
        return URI(self._update(port=port))
    
    def with_path(self, path: str) -> "URI":
        """设置路径"""
        return URI(self._update(path=path))
    
    def with_query(self, params: Dict[str, str]) -> "URI":
        """设置查询参数"""
        query = urllib.parse.urlencode(params)
        return URI(self._update(query=query))
    
    def add_param(self, key: str, value: str) -> "URI":
        """添加查询参数"""
        params = self.query
        params[key] = value
        return self.with_query(params)
    
    def remove_param(self, key: str) -> "URI":
        """删除查询参数"""
        params = self.query
        params.pop(key, None)
        return self.with_query(params)
    
    def _update(self, **kwargs) -> str:
        """更新URI组件"""
        from urllib.parse import urlunparse
        
        scheme = kwargs.get('scheme', self._parsed.scheme)
        netloc = kwargs.get('host', self._parsed.netloc)
        path = kwargs.get('path', self._parsed.path)
        params = kwargs.get('params', self._parsed.params)
        query = kwargs.get('query', self._parsed.query)
        fragment = kwargs.get('fragment', self._parsed.fragment)
        
        # 重建netloc
        if 'host' in kwargs or 'port' in kwargs:
            port = kwargs.get('port', self._parsed.port)
            username = kwargs.get('username', self._parsed.username)
            password = kwargs.get('password', self._parsed.password)
            
            netloc = ''
            if username:
                netloc += username
                if password:
                    netloc += f":{password}"
                netloc += '@'
            
            netloc += kwargs.get('host', self._parsed.hostname or '')
            
            if port:
                netloc += f":{port}"
        
        return urlunparse((scheme, netloc, path, params, query, fragment))
    
    def __str__(self) -> str:
        return self._uri
    
    def __repr__(self) -> str:
        return f"URI({self._uri})"


def parse_uri(uri: str) -> URI:
    """
    解析URI
    
    Args:
        uri: URI字符串
        
    Returns:
        URI对象
    """
    return URI(uri)


def build_uri(
    scheme: str = '',
    host: str = '',
    port: int = None,
    path: str = '',
    params: Dict[str, str] = None,
) -> str:
    """
    构建URI
    
    Args:
        scheme: 协议
        host: 主机
        port: 端口
        path: 路径
        params: 查询参数
        
    Returns:
        URI字符串
    """
    uri = URI('://')
    
    if scheme:
        uri = uri.with_scheme(scheme)
    if host:
        uri = uri.with_host(host)
    if port:
        uri = uri.with_port(port)
    if path:
        uri = uri.with_path(path)
    if params:
        uri = uri.with_query(params)
    
    return str(uri)


# 导出
__all__ = [
    "URI",
    "parse_uri",
    "build_uri",
]
