"""
Store - 存储
基于 Claude Code store.ts 设计

状态存储工具。
"""
from typing import Any, Callable, Dict, Optional


class Store:
    """
    状态存储
    
    简单的响应式存储。
    """
    
    def __init__(self, initial_state: Dict[str, Any] = None):
        """
        Args:
            initial_state: 初始状态
        """
        self._state = initial_state or {}
        self._listeners: Dict[str, list] = {}
        self._global_listeners: list = []
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取状态
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            状态值
        """
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        设置状态
        
        Args:
            key: 键
            value: 值
        """
        old_value = self._state.get(key)
        self._state[key] = value
        
        # 通知监听器
        self._notify(key, old_value, value)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        批量更新
        
        Args:
            updates: 要更新的键值对
        """
        for key, value in updates.items():
            self.set(key, value)
    
    def delete(self, key: str) -> bool:
        """
        删除状态
        
        Args:
            key: 键
            
        Returns:
            是否成功删除
        """
        if key in self._state:
            old_value = self._state[key]
            del self._state[key]
            self._notify(key, old_value, None)
            return True
        return False
    
    def subscribe(
        self,
        key: str,
        callback: Callable[[Any, Any], None],
    ) -> Callable:
        """
        订阅变更
        
        Args:
            key: 键
            callback: 回调 (oldValue, newValue)
            
        Returns:
            取消订阅函数
        """
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)
        
        return lambda: self._listeners[key].remove(callback)
    
    def subscribe_all(self, callback: Callable) -> Callable:
        """
        订阅所有变更
        
        Args:
            callback: 回调函数
            
        Returns:
            取消订阅函数
        """
        self._global_listeners.append(callback)
        return lambda: self._global_listeners.remove(callback)
    
    def _notify(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知监听器"""
        # 键监听器
        for callback in self._listeners.get(key, [])[:]:
            try:
                callback(old_value, new_value)
            except Exception:
                pass
        
        # 全局监听器
        for callback in self._global_listeners[:]:
            try:
                callback(key, old_value, new_value)
            except Exception:
                pass
    
    @property
    def state(self) -> Dict[str, Any]:
        """获取全部状态"""
        return dict(self._state)
    
    def clear(self) -> None:
        """清空状态"""
        self._state.clear()


class Patch:
    """
    状态补丁
    
    用于更新存储。
    """
    
    def __init__(self, store: Store):
        self._store = store
        self._updates: Dict[str, Any] = {}
    
    def set(self, key: str, value: Any) -> "Patch":
        """添加设置操作"""
        self._updates[key] = value
        return self
    
    def delete(self, key: str) -> "Patch":
        """添加删除操作"""
        self._updates[key] = None
        return self
    
    def apply(self) -> None:
        """应用补丁"""
        for key, value in self._updates.items():
            if value is None:
                self._store.delete(key)
            else:
                self._store.set(key, value)
        self._updates.clear()


def create_store(initial_state: Dict[str, Any] = None) -> Store:
    """
    创建存储
    
    Args:
        initial_state: 初始状态
        
    Returns:
        Store实例
    """
    return Store(initial_state)


# 导出
__all__ = [
    "Store",
    "Patch",
    "create_store",
]
