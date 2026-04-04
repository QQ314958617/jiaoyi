"""
Builder - 构建器
基于 Claude Code builder.ts 设计

构建器模式工具。
"""
from typing import Any, Callable, Dict, List


class Builder:
    """
    通用构建器
    
    链式调用构建对象。
    """
    
    def __init__(self):
        self._props: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any) -> "Builder":
        """设置属性"""
        self._props[key] = value
        return self
    
    def update(self, props: Dict[str, Any]) -> "Builder":
        """批量更新"""
        self._props.update(props)
        return self
    
    def build(self) -> Dict[str, Any]:
        """构建对象"""
        return dict(self._props)
    
    def reset(self) -> "Builder":
        """重置"""
        self._props.clear()
        return self


class TypeBuilder:
    """
    类型化构建器
    
    支持类型验证。
    """
    
    def __init__(self, schema: Dict[str, type]):
        """
        Args:
            schema: {属性名: 类型}
        """
        self._schema = schema
        self._props: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any) -> "TypeBuilder":
        """设置属性（带类型检查）"""
        if key in self._schema:
            expected = self._schema[key]
            if value is not None and not isinstance(value, expected):
                raise TypeError(f"Expected {expected.__name__}, got {type(value).__name__}")
        self._props[key] = value
        return self
    
    def required(self, key: str) -> "TypeBuilder":
        """标记为必需"""
        if key not in self._props or self._props[key] is None:
            raise ValueError(f"Required property missing: {key}")
        return self
    
    def build(self) -> Dict[str, Any]:
        """构建"""
        return dict(self._props)


def builder() -> Builder:
    """创建构建器"""
    return Builder()


class ChainBuilder:
    """
    链式构建器
    
    基于字典的链式调用。
    """
    
    def __init__(self, initial: Dict[str, Any] = None):
        self._data = initial or {}
    
    def set(self, key: str, value: Any) -> "ChainBuilder":
        """设置"""
        self._data[key] = value
        return self
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取"""
        return self._data.get(key, default)
    
    def delete(self, key: str) -> "ChainBuilder":
        """删除"""
        if key in self._data:
            del self._data[key]
        return self
    
    def merge(self, other: dict) -> "ChainBuilder":
        """合并"""
        self._data.update(other)
        return self
    
    def build(self) -> dict:
        """构建"""
        return dict(self._data)
    
    def __repr__(self) -> str:
        return f"ChainBuilder({self._data})"


class QueryBuilder:
    """
    查询构建器
    
    构建URL参数等。
    """
    
    def __init__(self):
        self._params: List[tuple] = []
    
    def add(self, key: str, value: Any) -> "QueryBuilder":
        """添加参数"""
        self._params.append((key, str(value)))
        return self
    
    def add_if(self, key: str, value: Any, condition: bool = True) -> "QueryBuilder":
        """条件添加"""
        if condition:
            self._params.append((key, str(value)))
        return self
    
    def build(self, separator: str = '&', encode: bool = True) -> str:
        """构建查询字符串"""
        parts = []
        for key, value in self._params:
            from urllib.parse import quote
            if encode:
                key = quote(key, safe='')
                value = quote(value, safe='')
            parts.append(f"{key}={value}")
        return separator.join(parts)


# 导出
__all__ = [
    "Builder",
    "TypeBuilder",
    "builder",
    "ChainBuilder",
    "QueryBuilder",
]
