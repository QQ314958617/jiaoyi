"""
State - 状态机
基于 Claude Code state.ts 设计

状态机工具。
"""
from typing import Any, Callable, Dict, List, Optional, Set


class StateMachine:
    """
    状态机
    
    管理有限状态和转换。
    """
    
    def __init__(self, initial_state: str):
        """
        Args:
            initial_state: 初始状态
        """
        self._state = initial_state
        self._initial_state = initial_state
        self._transitions: Dict[str, Dict[str, str]] = {}  # state -> {event: next_state}
        self._handlers: Dict[str, Dict[str, Callable]] = {}  # state -> {event: handler}
        self._entry_handlers: Dict[str, Callable] = {}
        self._exit_handlers: Dict[str, Callable] = {}
        self._listeners: List[Callable] = []
    
    def add_transition(
        self,
        from_state: str,
        event: str,
        to_state: str,
        handler: Callable = None,
    ) -> "StateMachine":
        """
        添加转换
        
        Args:
            from_state: 起始状态
            event: 事件名
            to_state: 目标状态
            handler: 处理函数
            
        Returns:
            self
        """
        if from_state not in self._transitions:
            self._transitions[from_state] = {}
            self._handlers[from_state] = {}
        
        self._transitions[from_state][event] = to_state
        if handler:
            self._handlers[from_state][event] = handler
        
        return self
    
    def add_state(
        self,
        state: str,
        entry_handler: Callable = None,
        exit_handler: Callable = None,
    ) -> "StateMachine":
        """
        添加状态
        
        Args:
            state: 状态名
            entry_handler: 进入处理
            exit_handler: 离开处理
            
        Returns:
            self
        """
        if state not in self._transitions:
            self._transitions[state] = {}
            self._handlers[state] = {}
        
        if entry_handler:
            self._entry_handlers[state] = entry_handler
        if exit_handler:
            self._exit_handlers[state] = exit_handler
        
        return self
    
    def on(self, event: str, *args, **kwargs) -> bool:
        """
        触发事件
        
        Args:
            event: 事件名
            
        Returns:
            是否成功转换
        """
        if self._state not in self._transitions:
            return False
        
        if event not in self._transitions[self._state]:
            return False
        
        old_state = self._state
        new_state = self._transitions[self._state][event]
        
        # 执行离开处理
        if old_state in self._exit_handlers:
            self._exit_handlers[old_state]()
        
        # 执行转换处理
        handler = self._handlers[self._state].get(event)
        if handler:
            result = handler(*args, **kwargs)
            if result is False:
                return False
        
        # 更新状态
        self._state = new_state
        
        # 执行进入处理
        if new_state in self._entry_handlers:
            self._entry_handlers[new_state]()
        
        # 通知监听器
        self._notify(old_state, new_state, event)
        
        return True
    
    def can(self, event: str) -> bool:
        """是否可以转换"""
        return (
            self._state in self._transitions and
            event in self._transitions[self._state]
        )
    
    @property
    def state(self) -> str:
        """当前状态"""
        return self._state
    
    def reset(self) -> None:
        """重置到初始状态"""
        self._state = self._initial_state
    
    def subscribe(self, listener: Callable) -> Callable:
        """
        订阅状态变化
        
        Args:
            listener: (old_state, new_state, event) -> None
            
        Returns:
            取消订阅函数
        """
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)
    
    def _notify(self, old_state: str, new_state: str, event: str) -> None:
        """通知监听器"""
        for listener in self._listeners[:]:
            try:
                listener(old_state, new_state, event)
            except Exception:
                pass


class State:
    """
    状态封装
    """
    
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return f"State({self.name})"


def create_state_machine(initial: str) -> StateMachine:
    """
    创建状态机
    
    Args:
        initial: 初始状态
        
    Returns:
        StateMachine实例
    """
    return StateMachine(initial)


# 导出
__all__ = [
    "StateMachine",
    "State",
    "create_state_machine",
]
