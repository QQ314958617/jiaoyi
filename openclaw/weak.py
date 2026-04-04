"""
Weak - 弱引用
基于 Claude Code weak.ts 设计

弱引用工具。
"""
import weakref
from typing import Any, Callable, Optional


class WeakRef:
    """
    弱引用封装
    """
    
    def __init__(self, obj: Any):
        self._ref = weakref.ref(obj)
    
    @property
    def alive(self) -> bool:
        """对象是否存活"""
        return self._ref() is not None
    
    @property
    def object(self) -> Optional[Any]:
        """获取对象"""
        return self._ref()
    
    def deref(self) -> Optional[Any]:
        """解引用"""
        return self._ref()
    
    def __call__(self) -> Optional[Any]:
        return self._ref()


class WeakMap:
    """
    弱引用映射表
    """
    
    def __init__(self):
        self._map = weakref.WeakValueDictionary()
    
    def set(self, key: Any, value: Any) -> None:
        """设置"""
        self._map[key] = value
    
    def get(self, key: Any, default: Any = None) -> Any:
        """获取"""
        return self._map.get(key, default)
    
    def has(self, key: Any) -> bool:
        """是否存在"""
        return key in self._map
    
    def delete(self, key: Any) -> bool:
        """删除"""
        if key in self._map:
            del self._map[key]
            return True
        return False


class WeakSet:
    """
    弱引用集合
    """
    
    def __init__(self):
        # 使用WeakValueDictionary实现
        self._refs = {}
    
    def add(self, obj: Any) -> None:
        """添加"""
        import uuid
        key = id(obj)
        self._refs[key] = obj
    
    def has(self, obj: Any) -> bool:
        """是否存在"""
        key = id(obj)
        return key in self._refs and self._refs[key] is obj
    
    def delete(self, obj: Any) -> bool:
        """删除"""
        key = id(obj)
        if key in self._refs:
            del self._refs[key]
            return True
        return False


class FinalizationGroup:
    """
    最终化组
    
    对象被垃圾回收时执行回调。
    """
    
    def __init__(self, callback: Callable):
        """
        Args:
            callback: 回调函数 (key) -> None
        """
        self._callback = callback
        self._refs = {}
    
    def register(self, obj: Any, key: Any) -> None:
        """注册对象"""
        import uuid
        ref_key = str(uuid.uuid4())
        self._refs[ref_key] = (weakref.ref(obj), key)
    
    def unregister(self, obj: Any) -> None:
        """取消注册"""
        import gc
        # 清理已回收的对象
        to_delete = []
        for ref_key, (ref, key) in self._refs.items():
            if ref() is None:
                to_delete.append(ref_key)
        
        for ref_key in to_delete:
            _, key = self._refs.pop(ref_key)
            self._callback(key)


# 导出
__all__ = [
    "WeakRef",
    "WeakMap",
    "WeakSet",
    "FinalizationGroup",
]
