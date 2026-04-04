"""
TokenBudget - Token预算
基于 Claude Code token_budget.ts 设计

Token预算管理工具。
"""
from typing import Optional


class TokenBudget:
    """
    Token预算管理器
    """
    
    def __init__(self, max_tokens: int = 100000):
        """
        Args:
            max_tokens: 最大Token数
        """
        self._max_tokens = max_tokens
        self._used = 0
        self._limit = max_tokens
    
    def use(self, tokens: int) -> int:
        """
        使用Token
        
        Args:
            tokens: 使用数量
            
        Returns:
            剩余Token
        """
        self._used += tokens
        return self.remaining
    
    def estimate(self, text: str) -> int:
        """
        估算文本Token数
        
        简单估算：中文约2字符=1Token，英文约4字符=1Token
        """
        import re
        chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
        english = len(re.findall(r'[a-zA-Z]', text))
        other = len(text) - chinese - english
        
        return int(chinese / 2 + english / 4 + other)
    
    def can_use(self, tokens: int) -> bool:
        """是否可以使用的Token"""
        return self._used + tokens <= self._limit
    
    def reset(self):
        """重置预算"""
        self._used = 0
    
    @property
    def used(self) -> int:
        """已使用"""
        return self._used
    
    @property
    def remaining(self) -> int:
        """剩余"""
        return max(0, self._limit - self._used)
    
    @property
    def percent_used(self) -> float:
        """使用百分比"""
        return (self._used / self._limit) * 100 if self._limit > 0 else 0


# 全局预算
_budget = TokenBudget()


def get_budget() -> TokenBudget:
    """获取全局预算"""
    return _budget


def estimate(text: str) -> int:
    """估算Token"""
    return _budget.estimate(text)


def can_use(tokens: int) -> bool:
    """是否可以"""
    return _budget.can_use(tokens)


def use(tokens: int) -> int:
    """使用Token"""
    return _budget.use(tokens)


def reset():
    """重置"""
    _budget.reset()


# 导出
__all__ = [
    "TokenBudget",
    "get_budget",
    "estimate",
    "can_use",
    "use",
    "reset",
]
