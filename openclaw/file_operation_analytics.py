"""
File Operation Analytics - 文件操作分析
基于 Claude Code fileOperationAnalytics.ts 设计

文件操作的隐私保护分析日志。
"""
import hashlib
from typing import Optional


MAX_CONTENT_HASH_SIZE = 100 * 1024  # 100KB


def hash_file_path(file_path: str) -> str:
    """
    对文件路径进行哈希（取前16字符）
    
    用于隐私保护的文件操作分析。
    
    Args:
        file_path: 文件路径
        
    Returns:
        SHA256哈希的前16个字符
    """
    return hashlib.sha256(file_path.encode()).hexdigest()[:16]


def hash_file_content(content: str) -> str:
    """
    对文件内容进行哈希
    
    用于去重和变更检测。
    
    Args:
        content: 文件内容
        
    Returns:
        完整的SHA256哈希
    """
    # 如果内容过大，只哈希前MAX_CONTENT_HASH_SIZE字节
    if len(content) > MAX_CONTENT_HASH_SIZE:
        content = content[:MAX_CONTENT_HASH_SIZE]
    
    return hashlib.sha256(content.encode()).hexdigest()


def log_file_operation(
    operation: str,
    tool: str,
    file_path: str,
    content: Optional[str] = None,
    op_type: Optional[str] = None,
) -> dict:
    """
    记录文件操作分析
    
    Args:
        operation: 操作类型 ('read', 'write', 'edit')
        tool: 工具名称
        file_path: 文件路径
        content: 文件内容（可选）
        op_type: 操作子类型 ('create', 'update')
        
    Returns:
        分析元数据字典
    """
    metadata = {
        'operation': operation,
        'tool': tool,
        'file_path_hash': hash_file_path(file_path),
    }
    
    # 只在内容存在且小于限制时哈希
    if content is not None and len(content) <= MAX_CONTENT_HASH_SIZE:
        metadata['content_hash'] = hash_file_content(content)
    
    if op_type is not None:
        metadata['type'] = op_type
    
    return metadata


# 导出
__all__ = [
    "MAX_CONTENT_HASH_SIZE",
    "hash_file_path",
    "hash_file_content",
    "log_file_operation",
]
