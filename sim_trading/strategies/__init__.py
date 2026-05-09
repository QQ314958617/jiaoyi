"""
蛋蛋多策略交易系统 - 策略框架
================================
策略基类 + 管理器
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


class BaseStrategy:
    """策略基类"""
    
    name: str = ""
    strategy_type: str = ""
    description: str = ""
    
    def __init__(self, strategy_id: int, config: dict = None):
        self.strategy_id = strategy_id
        self.config = config or {}
    
    def get_name(self) -> str:
        return self.name
    
    def get_type(self) -> str:
        return self.strategy_type
    
    def get_bj_time(self) -> datetime:
        """获取北京时间"""
        return datetime.now(timezone(timedelta(hours=8)))
    
    def is_trading_time(self) -> bool:
        """检查是否在交易时间"""
        bj = self.get_bj_time()
        t = bj.time()
        # 9:30-11:30 / 13:00-15:00
        from datetime import time as t_time
        return (t_time(9, 30) <= t <= t_time(11, 30) or
                t_time(13, 0) <= t <= t_time(15, 0))
    
    def get_strategy_type(self) -> str:
        return self.strategy_type


class StrategyRegistry:
    """策略注册表 - 管理所有可用策略类"""
    
    _strategies = {}
    
    @classmethod
    def register(cls, strategy_class):
        """注册策略类"""
        instance = strategy_class(strategy_id=0)
        cls._strategies[instance.get_type()] = strategy_class
        return strategy_class
    
    @classmethod
    def get_strategy_class(cls, strategy_type: str):
        """按类型获取策略类"""
        return cls._strategies.get(strategy_type)
    
    @classmethod
    def get_all_strategy_types(cls):
        """获取所有已注册的策略类型"""
        return list(cls._strategies.keys())
    
    @classmethod
    def instantiate(cls, strategy_type: str, strategy_id: int, config: dict = None):
        """实例化策略"""
        klass = cls.get_strategy_class(strategy_type)
        if klass:
            return klass(strategy_id, config or {})
        return None
