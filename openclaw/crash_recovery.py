"""
CrashRecovery - 崩溃恢复
基于 Claude Code crash_recovery.ts 设计

崩溃恢复工具。
"""
import os
import json
import time
from typing import Any, Optional


class CrashRecovery:
    """
    崩溃恢复
    
    保存和恢复状态。
    """
    
    def __init__(self, state_file: str = ".crash_recovery.json"):
        self._state_file = state_file
    
    def save(self, state: dict):
        """
        保存状态
        
        Args:
            state: 要保存的状态
        """
        data = {
            "state": state,
            "timestamp": time.time(),
        }
        
        with open(self._state_file, 'w') as f:
            json.dump(data, f)
    
    def load(self) -> Optional[dict]:
        """
        加载状态
        
        Returns:
            保存的状态或None
        """
        if not os.path.exists(self._state_file):
            return None
        
        try:
            with open(self._state_file, 'r') as f:
                data = json.load(f)
            return data.get("state")
        except (json.JSONDecodeError, IOError):
            return None
    
    def has_recovery(self) -> bool:
        """是否有恢复数据"""
        return os.path.exists(self._state_file)
    
    def clear(self):
        """清除恢复数据"""
        if os.path.exists(self._state_file):
            os.remove(self._state_file)
    
    def get_timestamp(self) -> Optional[float]:
        """获取保存时间戳"""
        if not os.path.exists(self._state_file):
            return None
        
        try:
            with open(self._state_file, 'r') as f:
                data = json.load(f)
            return data.get("timestamp")
        except (json.JSONDecodeError, IOError):
            return None


def save(state: dict, file: str = ".crash_recovery.json"):
    """保存状态"""
    recovery = CrashRecovery(file)
    recovery.save(state)


def load(file: str = ".crash_recovery.json") -> Optional[dict]:
    """加载状态"""
    recovery = CrashRecovery(file)
    return recovery.load()


# 导出
__all__ = [
    "CrashRecovery",
    "save",
    "load",
]
