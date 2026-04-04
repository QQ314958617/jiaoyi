"""
UUID - 唯一标识符
基于 Claude Code uuid.ts 设计

UUID工具。
"""
import uuid as _uuid


def generate() -> str:
    """生成UUID"""
    return str(_uuid.uuid4())


def generate_simple() -> str:
    """简短UUID（8字符）"""
    return _uuid.uuid4().hex[:8]


def from_string(value: str) -> str:
    """从字符串生成确定性UUID"""
    return str(_uuid.uuid5(_uuid.NAMESPACE_DNS, value))


def is_valid(value: str) -> bool:
    """检查是否为有效UUID"""
    try:
        _uuid.UUID(value)
        return True
    except ValueError:
        return False


def uuid1() -> str:
    """基于时间戳的UUID"""
    return str(_uuid.uuid1())


def uuid4() -> str:
    """随机UUID"""
    return str(_uuid.uuid4())


def uuid5(namespace: str, name: str) -> str:
    """基于SHA-1的UUID"""
    return str(_uuid.uuid5(_uuid.uuid5(_uuid.NAMESPACE_DNS, namespace), name))


class UUIDGenerator:
    """
    UUID生成器
    """
    
    def __init__(self, prefix: str = ""):
        """
        Args:
            prefix: 前缀
        """
        self._prefix = prefix
    
    def next(self) -> str:
        """生成下一个UUID"""
        return f"{self._prefix}{generate()}"
    
    def simple(self) -> str:
        """简短UUID"""
        return f"{self._prefix}{generate_simple()}"
    
    def named(self, name: str) -> str:
        """命名UUID"""
        return f"{self._prefix}{from_string(name)}"


# 导出
__all__ = [
    "generate",
    "generate_simple",
    "from_string",
    "is_valid",
    "uuid1",
    "uuid4",
    "uuid5",
    "UUIDGenerator",
]
