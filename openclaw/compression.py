"""
Compression - 压缩工具
基于 Claude Code compression.ts 设计

数据压缩工具。
"""
import base64
import zlib
from typing import Optional


def compress_gzip(data: bytes) -> bytes:
    """
    Gzip压缩
    
    Args:
        data: 原始数据
        
    Returns:
        压缩后的数据
    """
    return zlib.compress(data, level=6)


def decompress_gzip(data: bytes) -> bytes:
    """
    Gzip解压
    
    Args:
        data: 压缩数据
        
    Returns:
        原始数据
    """
    return zlib.decompress(data)


def compress_zlib(data: bytes) -> bytes:
    """
    Zlib压缩
    
    Args:
        data: 原始数据
        
    Returns:
        压缩后的数据
    """
    return zlib.compress(data)


def decompress_zlib(data: bytes) -> bytes:
    """
    Zlib解压
    
    Args:
        data: 压缩数据
        
    Returns:
        原始数据
    """
    return zlib.decompress(data)


def compress_base64(data: str) -> str:
    """
    Base64编码（不是压缩）
    
    Args:
        data: 字符串
        
    Returns:
        Base64编码字符串
    """
    return base64.b64encode(data.encode()).decode()


def decompress_base64(data: str) -> str:
    """
    Base64解码
    
    Args:
        data: Base64字符串
        
    Returns:
        原始字符串
    """
    return base64.b64decode(data.encode()).decode()


class CompressionStream:
    """
    压缩流
    
    流式压缩/解压。
    """
    
    def __init__(self, compress: bool = True):
        """
        Args:
            compress: True压缩，False解压
        """
        self._compress = compress
        self._obj = zlib.compressobj() if compress else zlib.decompressobj()
    
    def update(self, data: bytes) -> bytes:
        """处理数据"""
        if self._compress:
            return self._obj.compress(data)
        else:
            return self._obj.decompress(data)
    
    def flush(self) -> bytes:
        """完成处理"""
        if self._compress:
            return self._obj.flush()
        return b''


# 导出
__all__ = [
    "compress_gzip",
    "decompress_gzip",
    "compress_zlib",
    "decompress_zlib",
    "compress_base64",
    "decompress_base64",
    "CompressionStream",
]
