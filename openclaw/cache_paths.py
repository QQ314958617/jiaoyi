"""
Cache Paths - 缓存路径管理
基于 Claude Code cachePaths.ts 设计

管理Claude CLI的缓存目录结构。
"""
import os
from pathlib import Path
from typing import Optional


def _djb2_hash(s: str) -> int:
    """
    DJB2哈希算法
    
    Args:
        s: 字符串
        
    Returns:
        哈希值
    """
    hash_val = 5381
    for c in s:
        hash_val = ((hash_val << 5) + hash_val) + ord(c)
    return abs(hash_val)


# 最大规范化长度
MAX_SANITIZED_LENGTH = 200


def _sanitize_path(name: str) -> str:
    """
    规范化路径名
    
    Args:
        name: 原始名称
        
    Returns:
        规范化后的名称
    """
    # 只保留字母数字
    sanitized = ''.join(c if c.isalnum() else '-' for c in name)
    
    if len(sanitized) <= MAX_SANITIZED_LENGTH:
        return sanitized
    
    # 超长时截断并添加哈希
    hash_suffix = abs(_djb2_hash(name)) % (36 ** 6)
    return f"{sanitized[:MAX_SANITIZED_LENGTH]}-{hash_suffix:06x}"


def _get_project_dir(cwd: str) -> str:
    """
    获取项目目录标识
    
    Args:
        cwd: 当前工作目录
        
    Returns:
        项目目录标识
    """
    return _sanitize_path(cwd)


def _get_base_dir() -> str:
    """
    获取基础缓存目录
    
    Returns:
        基础缓存目录
    """
    # 优先使用环境变量
    if os.environ.get('CLAUDE_CACHE_DIR'):
        return os.environ['CLAUDE_CACHE_DIR']
    
    # 使用平台标准路径
    if os.name == 'nt':  # Windows
        base = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        return os.path.join(base, 'claude-cli', 'cache')
    elif os.name == 'posix':
        if os.uname().sysname == 'Darwin':  # macOS
            return os.path.expanduser('~/Library/Caches/claude-cli')
        else:  # Linux
            xdg_cache = os.environ.get('XDG_CACHE_HOME')
            if xdg_cache:
                return os.path.join(xdg_cache, 'claude-cli')
            return os.path.expanduser('~/.cache/claude-cli')
    
    # 默认
    return os.path.expanduser('~/.claude/cache')


class CachePaths:
    """
    缓存路径管理器
    """
    
    def __init__(self, cwd: Optional[str] = None):
        self._cwd = cwd or os.getcwd()
        self._project_dir = _get_project_dir(self._cwd)
        self._base_dir = _get_base_dir()
    
    @property
    def project_dir(self) -> str:
        """项目缓存目录"""
        return self._project_dir
    
    @property
    def base_logs(self) -> str:
        """基础日志目录"""
        return os.path.join(self._base_dir, self._project_dir)
    
    @property
    def errors(self) -> str:
        """错误日志目录"""
        return os.path.join(self._base_dir, self._project_dir, 'errors')
    
    @property
    def messages(self) -> str:
        """消息缓存目录"""
        return os.path.join(self._base_dir, self._project_dir, 'messages')
    
    def mcp_logs(self, server_name: str) -> str:
        """
        MCP服务器日志目录
        
        Args:
            server_name: 服务器名称
            
        Returns:
            日志目录路径
        """
        safe_name = _sanitize_path(server_name)
        return os.path.join(self._base_dir, self._project_dir, f'mcp-logs-{safe_name}')
    
    def ensure_dirs(self) -> None:
        """确保所有必要目录存在"""
        dirs = [
            self.base_logs,
            self.errors,
            self.messages,
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)


# 全局缓存路径实例
_cache_paths: Optional[CachePaths] = None


def get_cache_paths(cwd: Optional[str] = None) -> CachePaths:
    """
    获取缓存路径管理器
    
    Args:
        cwd: 当前工作目录
        
    Returns:
        缓存路径管理器
    """
    global _cache_paths
    if _cache_paths is None:
        _cache_paths = CachePaths(cwd)
    return _cache_paths


# 导出
__all__ = [
    "CachePaths",
    "get_cache_paths",
    "_sanitize_path",
]
