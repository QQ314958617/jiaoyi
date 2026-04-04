"""
SemVer - 语义化版本
基于 Claude Code semver.ts 设计

语义化版本工具。
"""
import re
from typing import Tuple


class SemVer:
    """
    语义化版本
    
    主版本.次版本.修订号 [-预发布版本] [+构建元数据]
    """
    
    def __init__(self, major: int, minor: int, patch: int,
                 prerelease: str = "", build: str = ""):
        """
        Args:
            major: 主版本
            minor: 次版本
            patch: 修订号
            prerelease: 预发布标签
            build: 构建元数据
        """
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease
        self.build = build
    
    @staticmethod
    def parse(version: str) -> "SemVer":
        """
        解析版本字符串
        
        Args:
            version: 版本字符串 (如 "1.2.3-alpha")
            
        Returns:
            SemVer实例
        """
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.]+))?(?:\+(.+))?$'
        match = re.match(pattern, version)
        
        if not match:
            raise ValueError(f"Invalid semver: {version}")
        
        return SemVer(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            match.group(4) or "",
            match.group(5) or ""
        )
    
    def __str__(self) -> str:
        """转为字符串"""
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            v += f"-{self.prerelease}"
        if self.build:
            v += f"+{self.build}"
        return v
    
    def __repr__(self) -> str:
        return f"SemVer({self.major}, {self.minor}, {self.patch})"
    
    def _compare(self, other: "SemVer") -> int:
        """比较版本"""
        # 主次补丁
        for v1, v2 in [(self.major, other.major),
                        (self.minor, other.minor),
                        (self.patch, other.patch)]:
            if v1 < v2:
                return -1
            if v1 > v2:
                return 1
        
        # 预发布版本
        if self.prerelease and not other.prerelease:
            return -1
        if not self.prerelease and other.prerelease:
            return 1
        if self.prerelease < other.prerelease:
            return -1
        if self.prerelease > other.prerelease:
            return 1
        
        return 0
    
    def __eq__(self, other) -> bool:
        return self._compare(other) == 0
    
    def __lt__(self, other) -> bool:
        return self._compare(other) < 0
    
    def __le__(self, other) -> bool:
        return self._compare(other) <= 0
    
    def __gt__(self, other) -> bool:
        return self._compare(other) > 0
    
    def __ge__(self, other) -> bool:
        return self._compare(other) >= 0
    
    def bump_major(self) -> "SemVer":
        """主版本+1"""
        return SemVer(self.major + 1, 0, 0)
    
    def bump_minor(self) -> "SemVer":
        """次版本+1"""
        return SemVer(self.major, self.minor + 1, 0)
    
    def bump_patch(self) -> "SemVer":
        """修订号+1"""
        return SemVer(self.major, self.minor, self.patch + 1)


def compare(a: str, b: str) -> int:
    """比较两个版本"""
    return SemVer.parse(a)._compare(SemVer.parse(b))


def satisfies(version: str, range_: str) -> bool:
    """
    检查版本是否满足范围
    
    Args:
        version: 版本
        range_: 范围（如 ">=1.0.0 <2.0.0"）
        
    Returns:
        是否满足
    """
    v = SemVer.parse(version)
    
    # 简化版，仅支持 ^ ~ >
    range_ = range_.strip()
    
    if range_.startswith('^'):
        constraint = range_[1:]
        c = SemVer.parse(constraint)
        return v.major == c.major and v.minor >= c.minor and v.patch >= c.patch
    if range_.startswith('~'):
        constraint = range_[1:]
        c = SemVer.parse(constraint)
        return v.major == c.major and v.minor == c.minor and v.patch >= c.patch
    
    # 简单比较
    ops = ['>=', '<=', '>', '<', '==']
    for op in ops:
        if range_.startswith(op):
            other_ver = range_[len(op):].strip()
            other = SemVer.parse(other_ver)
            if op == '>=':
                return v >= other
            elif op == '<=':
                return v <= other
            elif op == '>':
                return v > other
            elif op == '<':
                return v < other
            elif op == '==':
                return v == other
    
    return False


# 导出
__all__ = [
    "SemVer",
    "compare",
    "satisfies",
]
