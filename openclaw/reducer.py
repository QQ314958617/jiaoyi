"""
Reducer - 归约器
基于 Claude Code reducer.ts 设计

状态归约工具。
"""
from typing import Any, Callable, Dict, List, TypeVar

S = TypeVar('S')
A = TypeVar('A')
T = TypeVar('T')


class Reducer:
    """
    状态归约器
    
    基于动作类型归约状态。
    """
    
    def __init__(self, initial_state: S, handlers: Dict[str, Callable] = None):
        """
        Args:
            initial_state: 初始状态
            handlers: {action_type: reducer_fn} 映射
        """
        self._state = initial_state
        self._handlers = handlers or {}
        self._listeners: List[Callable] = []
    
    def register(self, action_type: str, handler: Callable[[S, Any], S]) -> None:
        """
        注册处理器
        
        Args:
            action_type: 动作类型
            handler: 处理函数 (state, action) -> new_state
        """
        self._handlers[action_type] = handler
    
    def dispatch(self, action_type: str, payload: Any = None) -> None:
        """
        分发动作
        
        Args:
            action_type: 动作类型
            payload: 动作数据
        """
        if action_type in self._handlers:
            old_state = self._state
            self._state = self._handlers[action_type](self._state, payload)
            self._notify(old_state, self._state, action_type, payload)
    
    def get_state(self) -> S:
        """获取当前状态"""
        return self._state
    
    def set_state(self, state: S) -> None:
        """设置状态"""
        old_state = self._state
        self._state = state
        self._notify(old_state, state, "__set__", None)
    
    def subscribe(self, listener: Callable) -> Callable:
        """
        订阅状态变更
        
        Args:
            listener: (old_state, new_state, action_type, payload) -> None
            
        Returns:
            取消订阅函数
        """
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)
    
    def _notify(self, old_state: S, new_state: S, action_type: str, payload: Any) -> None:
        """通知监听器"""
        for listener in self._listeners[:]:
            try:
                listener(old_state, new_state, action_type, payload)
            except Exception:
                pass


class Action:
    """
    动作封装
    """
    
    def __init__(self, type: str, payload: Any = None):
        self.type = type
        self.payload = payload


def create_action(type: str, payload: Any = None) -> Action:
    """
    创建动作
    
    Args:
        type: 动作类型
        payload: 动作数据
        
    Returns:
        Action实例
    """
    return Action(type, payload)


class Store:
    """
    简单状态存储
    
    基于reducer模式。
    """
    
    def __init__(self, reducer: Callable):
        self._reducer = reducer
        self._state = None
        self._listeners: List[Callable] = []
    
    def dispatch(self, action: Action) -> None:
        """分发动作"""
        old_state = self._state
        self._state = self._reducer(self._state, action)
        
        if old_state != self._state:
            for listener in self._listeners[:]:
                try:
                    listener(self._state)
                except Exception:
                    pass
    
    def get_state(self) -> S:
        """获取状态"""
        return self._state
    
    def subscribe(self, listener: Callable) -> Callable:
        """订阅"""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)


# 导出
__all__ = [
    "Reducer",
    "Action",
    "create_action",
    "Store",
]
