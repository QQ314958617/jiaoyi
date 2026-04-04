"""
ModelCost - 模型成本
基于 Claude Code model_cost.ts 设计

模型成本计算工具。
"""
from typing import Dict, Optional


# 模型定价（$/1M tokens）
MODEL_PRICES = {
    # Claude
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3.5-haiku": {"input": 0.8, "output": 4.0},
    
    # GPT
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    
    # Gemini
    "gemini-pro": {"input": 0.25, "output": 0.5},
    "gemini-ultra": {"input": 2.0, "output": 2.0},
    
    # MiniMax
    "minimax": {"input": 0.1, "output": 0.1},
    "MiniMax-M2": {"input": 0.1, "output": 0.1},
}


def get_price(model: str) -> Optional[Dict[str, float]]:
    """获取模型价格"""
    return MODEL_PRICES.get(model.lower())


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    计算成本
    
    Args:
        model: 模型名
        input_tokens: 输入Token数
        output_tokens: 输出Token数
        
    Returns:
        成本（美元）
    """
    price = get_price(model)
    if price is None:
        return 0.0
    
    input_cost = (input_tokens / 1_000_000) * price["input"]
    output_cost = (output_tokens / 1_000_000) * price["output"]
    
    return input_cost + output_cost


def calculate_input_cost(model: str, tokens: int) -> float:
    """计算输入成本"""
    price = get_price(model)
    if price is None:
        return 0.0
    return (tokens / 1_000_000) * price["input"]


def calculate_output_cost(model: str, tokens: int) -> float:
    """计算输出成本"""
    price = get_price(model)
    if price is None:
        return 0.0
    return (tokens / 1_000_000) * price["output"]


def estimate_cost(model: str, text: str, is_output: bool = False) -> float:
    """
    估算文本成本
    
    Args:
        model: 模型
        text: 文本
        is_output: 是否为输出
    """
    # 简单估算
    tokens = len(text) // 4
    
    if is_output:
        return calculate_output_cost(model, tokens)
    return calculate_input_cost(model, tokens)


class CostTracker:
    """成本追踪器"""
    
    def __init__(self, model: str = "minimax"):
        self._model = model
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
    
    def add(self, input_tokens: int, output_tokens: int = 0):
        """添加使用"""
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_cost += calculate_cost(self._model, input_tokens, output_tokens)
    
    @property
    def total_cost(self) -> float:
        return self._total_cost
    
    @property
    def total_tokens(self) -> int:
        return self._total_input_tokens + self._total_output_tokens
    
    def reset(self):
        """重置"""
        self._total_cost = 0.0
        self._total_input_tokens = 0
        self._total_output_tokens = 0


# 全局追踪器
_cost_tracker = CostTracker()


def get_tracker() -> CostTracker:
    return _cost_tracker


def add_usage(input_tokens: int, output_tokens: int = 0):
    _cost_tracker.add(input_tokens, output_tokens)


# 导出
__all__ = [
    "MODEL_PRICES",
    "get_price",
    "calculate_cost",
    "calculate_input_cost",
    "calculate_output_cost",
    "estimate_cost",
    "CostTracker",
    "get_tracker",
    "add_usage",
]
