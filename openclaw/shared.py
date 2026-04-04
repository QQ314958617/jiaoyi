"""
Shared - 共享值
基于 Claude Code shared.ts 设计

跨上下文共享数据。
"""
import asyncio
from typing import Any, Callable, Dict, Optional


class Shared:
    """
    共享值
    
    跨模块共享数据。
    """
    
    def __init__(self):
        self._values: Dict[str, Any] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._default_factories: Dict[str, Callable] = {}
        self._global_lock = asyncio.Lock()
    
    def set(self, key: str, value: Any) -> None:
        """设置值"""
        self._values[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取值"""
        return self._values.get(key, default)
    
    def get_or_create(
        self,
        key: str,
        factory: Callable[[], Any],
    ) -> Any:
        """获取或创建"""
        if key not in self._values:
            self._values[key] = factory()
        return self._values[key]
    
    async def get_or_create_async(
        self,
        key: str,
        factory: Callable[[], Any],
    ) -> Any:
        """异步获取或创建"""
        if key not in self._values:
            async with self._global_lock:
                # 双重检查
                if key not in self._values:
                    result = factory()
                    if asyncio.iscoroutine(result):
                        result = await result
                    self._values[key] = result
        return self._values[key]
    
    def delete(self, key: str) -> bool:
        """删除值"""
        if key in self._values:
            del self._values[key]
            return True
        return False
    
    def has(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._values
    
    def keys(self):
        """获取所有键"""
        return list(self._values.keys())
    
    def clear(self) -> None:
        """清空"""
        self._values.clear()
    
    def update(self, data: dict) -> None:
        """批量更新"""
        self._values.update(data)


class SharedMap(Shared):
    """
    共享映射
    
    带类型的共享映射。
    """
    
    def __init__(self):
        super().__init__()
        self._type_hints: Dict[str, type] = {}
    
    def set_type(self, key: str, type_hint: type) -> None:
        """设置类型提示"""
        self._type_hints[key] = type_hint
    
    def get_typed(self, key: str, default: Any = None) -> Any:
        """获取带类型检查"""
        value = self.get(key, default)
        if key in self._type_hints and value is not None:
            expected = self._type_hints[key]
            if not isinstance(value, expected):
                raise TypeError(
                    f"Expected {expected}, got {type(value)}"
                )
        return value


# 全局实例
_shared = Shared()


def shared_get(key: str, default: Any = None) -> Any:
    """全局获取"""
    return _shared.get(key, default)


def shared_set(key: str, value: Any) -> None:
    """全局设置"""
    _shared.set(key, value)


def shared_has(key: str) -> bool:
    """全局检查"""
    return _shared.has(key)


# 导出
__all__ = [
    "Shared",
    "SharedMap",
    "shared_get",
    "shared_set",
    "shared_has",
]
