"""
Atom - 原子化
基于 Claude Code atom.ts 设计

原子操作工具。
"""
import threading
from typing import Any, Callable, TypeVar

T = TypeVar('T')


class Atom:
    """
    原子值
    
    线程安全的可变值。
    """
    
    def __init__(self, value: T):
        """
        Args:
            value: 初始值
        """
        self._value = value
        self._lock = threading.Lock()
    
    def get(self) -> T:
        """获取值"""
        with self._lock:
            return self._value
    
    def set(self, value: T) -> None:
        """设置值"""
        with self._lock:
            self._value = value
    
    def update(self, fn: Callable[[T], T]) -> T:
        """
        更新值
        
        Args:
            fn: 更新函数
            
        Returns:
            新值
        """
        with self._lock:
            self._value = fn(self._value)
            return self._value
    
    def swap(self, fn: Callable[[T], T]) -> T:
        """swap的别名"""
        return self.update(fn)
    
    def compare_and_set(self, expected: T, new_value: T) -> bool:
        """
        CAS操作
        
        Args:
            expected: 期望值
            new_value: 新值
            
        Returns:
            是否成功
        """
        with self._lock:
            if self._value == expected:
                self._value = new_value
                return True
            return False
    
    def __iadd__(self, delta: T) -> T:
        """+= 操作"""
        return self.update(lambda x: x + delta)
    
    def __isub__(self, delta: T) -> T:
        """-= 操作"""
        return self.update(lambda x: x - delta)
    
    def __imul__(self, factor: T) -> T:
        """*= 操作"""
        return self.update(lambda x: x * factor)
    
    def __itruediv__(self, divisor: T) -> T:
        """/= 操作"""
        return self.update(lambda x: x / divisor)


class AtomRef(Atom):
    """
    原子引用
    
    类似Atom但支持任意对象。
    """
    pass


def atom(value: T) -> Atom:
    """
    创建原子值
    
    Args:
        value: 初始值
        
    Returns:
        Atom实例
    """
    return Atom(value)


class DerivedAtom:
    """
    派生原子
    
    基于其他原子计算。
    """
    
    def __init__(self, fn: Callable, *atoms: Atom):
        """
        Args:
            fn: 计算函数
            *atoms: 依赖的原子
        """
        self._fn = fn
        self._atoms = atoms
        self._cached_value = None
        self._lock = threading.Lock()
    
    def get(self) -> Any:
        """获取值（重新计算）"""
        with self._lock:
            # 简单缓存：依赖没变就返回缓存
            values = [atom.get() for atom in self._atoms]
            self._cached_value = self._fn(*values)
            return self._cached_value


# 导出
__all__ = [
    "Atom",
    "AtomRef",
    "atom",
    "DerivedAtom",
]
