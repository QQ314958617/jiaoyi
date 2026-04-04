"""
Version - 版本
基于 Claude Code version.ts 设计

版本比较工具。
"""
import re
from typing import List, Tuple


class Version:
    """
    版本号
    
    语义化版本支持。
    """
    
    def __init__(self, version: str):
        """
        Args:
            version: 版本字符串 (如 "1.2.3-beta.1")
        """
        self._original = version
        self._parse(version)
    
    def _parse(self, version: str) -> None:
        """解析版本字符串"""
        # 匹配: major.minor.patch[-prerelease][+build]
        pattern = r'(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?'
        match = re.match(pattern, version)
        
        if not match:
            self.major = 0
            self.minor = 0
            self.patch = 0
            self.prerelease = ''
            self.build = ''
            return
        
        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))
        self.prerelease = match.group(4) or ''
        self.build = match.group(5) or ''
    
    def _compare_part(self, a: str, b: str) -> int:
        """比较版本部分"""
        if not a and not b:
            return 0
        
        if not a:
            return 1
        if not b:
            return -1
        
        # 数字 vs 字母
        a_is_num = a.isdigit()
        b_is_num = b.isdigit()
        
        if a_is_num and b_is_num:
            return int(a) - int(b)
        
        if a_is_num:
            return -1
        if b_is_num:
            return 1
        
        return -1 if a < b else (1 if a > b else 0)
    
    def _compare_prerelease(self, a: str, b: str) -> int:
        """比较预发布版本"""
        if not a and not b:
            return 0
        
        if not a:
            return 1
        if not b:
            return -1
        
        a_parts = re.split(r'[.-]', a)
        b_parts = re.split(r'[.-]', b)
        
        for i in range(max(len(a_parts), len(b_parts))):
            a_part = a_parts[i] if i < len(a_parts) else ''
            b_part = b_parts[i] if i < len(b_parts) else ''
            
            result = self._compare_part(a_part, b_part)
            if result != 0:
                return result
        
        return 0
    
    def compare(self, other: "Version") -> int:
        """
        比较版本
        
        Returns:
            -1: self < other
             0: self == other
             1: self > other
        """
        # 比较主版本
        if self.major != other.major:
            return -1 if self.major < other.major else 1
        
        # 比较次版本
        if self.minor != other.minor:
            return -1 if self.minor < other.minor else 1
        
        # 比较补丁版本
        if self.patch != other.patch:
            return -1 if self.patch < other.patch else 1
        
        # 比较预发布版本
        return self._compare_prerelease(self.prerelease, other.prerelease)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Version):
            return False
        return self.compare(other) == 0
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, Version):
            return False
        return self.compare(other) < 0
    
    def __le__(self, other) -> bool:
        return self == other or self < other
    
    def __gt__(self, other) -> bool:
        return other < self
    
    def __ge__(self, other) -> bool:
        return self == other or self > other
    
    def __repr__(self) -> str:
        return f"Version({self._original})"
    
    def __str__(self) -> str:
        return self._original
    
    def is_prerelease(self) -> bool:
        """是否为预发布版本"""
        return bool(self.prerelease)


def compare_versions(v1: str, v2: str) -> int:
    """
    比较两个版本字符串
    
    Args:
        v1: 版本1
        v2: 版本2
        
    Returns:
        -1, 0, 1
    """
    v1_obj = Version(v1)
    v2_obj = Version(v2)
    return v1_obj.compare(v2_obj)


def is_compatible(current: str, required: str) -> bool:
    """
    检查版本兼容性
    
    Args:
        current: 当前版本
        required: 要求的版本
        
    Returns:
        是否兼容
    """
    curr = Version(current)
    req = Version(required)
    
    # 主版本必须匹配
    if curr.major != req.major:
        return False
    
    # 次版本必须 >= 要求
    if curr.minor < req.minor:
        return False
    
    # 如果次版本相等，补丁版本必须 >= 要求
    if curr.minor == req.minor and curr.patch < req.patch:
        return False
    
    return True


# 导出
__all__ = [
    "Version",
    "compare_versions",
    "is_compatible",
]
