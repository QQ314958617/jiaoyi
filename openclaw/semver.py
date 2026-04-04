"""
SemVer - 语义化版本
基于 Claude Code semver.ts 设计

完整的语义化版本支持。
"""
import re
from typing import Optional


class SemVer:
    """
    语义化版本
    
    支持完整的语义化版本规范。
    """
    
    def __init__(
        self,
        major: int,
        minor: int,
        patch: int,
        prerelease: str = '',
        build: str = '',
    ):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.prerelease = prerelease
        self.build = build
    
    @classmethod
    def parse(cls, version: str) -> "SemVer":
        """解析版本字符串"""
        pattern = r'(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?'
        match = re.match(pattern, version)
        
        if not match:
            raise ValueError(f"Invalid semver: {version}")
        
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4) or '',
            build=match.group(5) or '',
        )
    
    def format(self) -> str:
        """格式化为字符串"""
        result = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            result += f"-{self.prerelease}"
        if self.build:
            result += f"+{self.build}"
        return result
    
    def _compare_prerelease(self, other: "SemVer") -> int:
        """比较预发布版本"""
        if not self.prerelease and not other.prerelease:
            return 0
        if not self.prerelease:
            return 1
        if not other.prerelease:
            return -1
        
        self_parts = self._parse_parts()
        other_parts = other._parse_parts()
        
        for i in range(max(len(self_parts), len(other_parts))):
            s = self_parts[i] if i < len(self_parts) else None
            o = other_parts[i] if i < len(other_parts) else None
            
            if s is None:
                return -1
            if o is None:
                return 1
            
            if s < o:
                return -1
            if s > o:
                return 1
        
        return 0
    
    def _parse_parts(self) -> list:
        """解析预发布版本部分"""
        if not self.prerelease:
            return []
        
        result = []
        current = ''
        
        for char in self.prerelease:
            if char.isdigit():
                current += char
            else:
                if current:
                    result.append(int(current))
                    current = ''
                result.append(char)
        
        if current:
            result.append(int(current))
        
        return result
    
    def compare(self, other: "SemVer") -> int:
        """比较版本"""
        if self.major != other.major:
            return -1 if self.major < other.major else 1
        if self.minor != other.minor:
            return -1 if self.minor < other.minor else 1
        if self.patch != other.patch:
            return -1 if self.patch < other.patch else 1
        return self._compare_prerelease(other)
    
    def is_prerelease(self) -> bool:
        return bool(self.prerelease)
    
    def next_major(self) -> "SemVer":
        return SemVer(self.major + 1, 0, 0)
    
    def next_minor(self) -> "SemVer":
        return SemVer(self.major, self.minor + 1, 0)
    
    def next_patch(self) -> "SemVer":
        return SemVer(self.major, self.minor, self.patch + 1)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, SemVer):
            return False
        return self.compare(other) == 0
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, SemVer):
            return False
        return self.compare(other) < 0
    
    def __le__(self, other) -> bool:
        return self == other or self < other
    
    def __gt__(self, other) -> bool:
        return other < self
    
    def __ge__(self, other) -> bool:
        return self == other or self > other
    
    def __repr__(self) -> str:
        return f"SemVer({self.format()})"
    
    def __str__(self) -> str:
        return self.format()


def valid(version: str) -> Optional[SemVer]:
    """验证并解析版本"""
    try:
        return SemVer.parse(version)
    except ValueError:
        return None


def inc(version: str, release: str = 'patch') -> str:
    """增加版本号"""
    semver = SemVer.parse(version)
    if release == 'major':
        return str(semver.next_major())
    if release == 'minor':
        return str(semver.next_minor())
    return str(semver.next_patch())


__all__ = ['SemVer', 'valid', 'inc']
