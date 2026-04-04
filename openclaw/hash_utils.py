"""
Hash Utilities - 哈希工具
基于 Claude Code hash.ts 设计

提供各种哈希函数。
"""
import hashlib
from typing import Optional


def djb2_hash(s: str) -> int:
    """
    DJB2哈希算法
    
    快速非加密哈希，返回有符号32位整数。
    跨运行时确定（不同于Bun.hash）。
    
    Args:
        s: 字符串
        
    Returns:
        有符号32位哈希值
    """
    hash_val = 0
    for i in range(len(s)):
        hash_val = ((hash_val << 5) - hash_val + ord(s[i])) & 0xFFFFFFFF
    # 转换为有符号整数
    if hash_val & 0x80000000:
        hash_val -= 0x100000000
    return hash_val


def hash_content(content: str) -> str:
    """
    内容哈希（变更检测）
    
    使用Bun.hash（如果可用），否则使用SHA256。
    
    Args:
        content: 内容
        
    Returns:
        十六进制哈希字符串
    """
    # 尝试使用更快的哈希
    try:
        import sys
        if 'Bun' in type(sys).__module__ if hasattr(sys, 'Bun') else False:
            # Bun环境
            pass  # Bun.hash(content).toString()
    except Exception:
        pass
    
    # 使用SHA256
    return hashlib.sha256(content.encode()).hexdigest()


def hash_pair(a: str, b: str) -> str:
    """
    两个字符串的组合哈希
    
    使用SHA256增量更新。
    
    Args:
        a: 第一个字符串
        b: 第二个字符串
        
    Returns:
        十六进制哈希字符串
    """
    h = hashlib.sha256()
    h.update(a.encode())
    h.update(b.encode())
    return h.hexdigest()


def md5_hash(s: str) -> str:
    """
    MD5哈希
    
    Args:
        s: 字符串
        
    Returns:
        十六进制MD5字符串
    """
    return hashlib.md5(s.encode()).hexdigest()


def sha256_hash(s: str) -> str:
    """
    SHA256哈希
    
    Args:
        s: 字符串
        
    Returns:
        十六进制SHA256字符串
    """
    return hashlib.sha256(s.encode()).hexdigest()


# 导出
__all__ = [
    "djb2_hash",
    "hash_content",
    "hash_pair",
    "md5_hash",
    "sha256_hash",
]
