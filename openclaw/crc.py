"""
CRC - CRC校验
基于 Claude Code crc.ts 设计

CRC校验工具。
"""
import zlib


def crc32(data: bytes) -> int:
    """
    CRC32校验
    
    Args:
        data: 字节数据
        
    Returns:
        CRC32值
    """
    return zlib.crc32(data) & 0xffffffff


def crc32_hex(data: bytes) -> str:
    """
    CRC32校验（十六进制）
    
    Args:
        data: 字节数据
        
    Returns:
        十六进制CRC32字符串
    """
    return format(crc32(data), '08x')


def adler32(data: bytes) -> int:
    """
    Adler32校验
    
    Args:
        data: 字节数据
        
    Returns:
        Adler32值
    """
    return zlib.adler32(data) & 0xffffffff


def adler32_hex(data: bytes) -> str:
    """
    Adler32校验（十六进制）
    
    Args:
        data: 字节数据
        
    Returns:
        十六进制Adler32字符串
    """
    return format(adler32(data), '08x')


class CRCCalculator:
    """
    CRC计算器
    """
    
    def __init__(self, polynomial: int = 0xedb88320):
        """
        Args:
            polynomial: 多项式（默认CRC32）
        """
        self._table = self._build_table(polynomial)
        self._value = 0xffffffff
    
    def _build_table(self, polynomial: int) -> list:
        """构建查找表"""
        table = []
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ polynomial
                else:
                    crc >>= 1
            table.append(crc)
        return table
    
    def update(self, data: bytes) -> None:
        """更新数据"""
        for byte in data:
            self._value = self._table[(self._value ^ byte) & 0xff] ^ (self._value >> 8)
    
    def digest(self) -> int:
        """获取校验值"""
        return self._value ^ 0xffffffff
    
    def hexdigest(self) -> str:
        """获取十六进制校验值"""
        return format(self.digest(), '08x')


# 导出
__all__ = [
    "crc32",
    "crc32_hex",
    "adler32",
    "adler32_hex",
    "CRCCalculator",
]
