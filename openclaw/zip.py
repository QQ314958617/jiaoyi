"""
Zip - 压缩
基于 Claude Code zip.ts 设计

压缩工具。
"""
import gzip
import zlib
from typing import List


def gzip_compress(data: bytes) -> bytes:
    """
    GZIP压缩
    
    Args:
        data: 原始数据
        
    Returns:
        压缩数据
    """
    return gzip.compress(data)


def gzip_decompress(data: bytes) -> bytes:
    """
    GZIP解压
    
    Args:
        data: 压缩数据
        
    Returns:
        原始数据
    """
    return gzip.decompress(data)


def deflate(data: bytes) -> bytes:
    """
    DEFLATE压缩
    
    Args:
        data: 原始数据
        
    Returns:
        压缩数据
    """
    return zlib.compress(data)


def inflate(data: bytes) -> bytes:
    """
    DEFLATE解压
    
    Args:
        data: 压缩数据
        
    Returns:
        原始数据
    """
    return zlib.decompress(data)


def crc32(data: bytes) -> int:
    """
    CRC32校验
    
    Args:
        data: 数据
        
    Returns:
        CRC32值
    """
    return zlib.crc32(data)


def adler32(data: bytes) -> int:
    """
    Adler32校验
    
    Args:
        data: 数据
        
    Returns:
        Adler32值
    """
    return zlib.adler32(data)


class GzipFile:
    """GZIP文件包装"""
    
    def __init__(self, filepath: str, mode: str = 'r'):
        """
        Args:
            filepath: 文件路径
            mode: 模式 ('r', 'rb', 'w', 'wb')
        """
        self._filepath = filepath
        self._mode = mode
    
    def read(self) -> bytes:
        """读取"""
        with gzip.open(self._filepath, 'rb') as f:
            return f.read()
    
    def write(self, data: bytes) -> None:
        """写入"""
        with gzip.open(self._filepath, 'wb') as f:
            f.write(data)
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


# 导出
__all__ = [
    "gzip_compress",
    "gzip_decompress",
    "deflate",
    "inflate",
    "crc32",
    "adler32",
    "GzipFile",
]
