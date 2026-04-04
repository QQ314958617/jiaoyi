"""
Model Allowlist - 模型允许列表
基于 Claude Code modelAllowlist.ts 设计

检查模型是否在允许列表中。
"""
from typing import List, Optional


# 默认允许的模型列表
DEFAULT_ALLOWED_MODELS: List[str] = [
    'claude-opus-4-6-20251120',
    'claude-sonnet-4-6-20251120',
    'claude-haiku-4-6-20251120',
    'claude-opus-4-5-20251120',
    'claude-sonnet-4-5-20251120',
    'claude-haiku-4-5-20251120',
    # 别名
    'opus',
    'sonnet',
    'haiku',
    'opus4',
    'sonnet4',
    'haiku4',
]


# 允许列表
_allowed_models: List[str] = []


def is_model_allowed(model: str) -> bool:
    """
    检查模型是否在允许列表中
    
    Args:
        model: 模型名
        
    Returns:
        是否允许
    """
    if not _allowed_models:
        return True  # 默认允许所有
    
    model_lower = model.lower()
    
    # 检查完整名称
    if model_lower in [m.lower() for m in _allowed_models]:
        return True
    
    # 检查别名
    if model_lower in ['opus', 'sonnet', 'haiku']:
        return True
    
    return False


def set_allowed_models(models: List[str]) -> None:
    """
    设置允许的模型列表
    
    Args:
        models: 模型列表
    """
    global _allowed_models
    _allowed_models = list(models)


def get_allowed_models() -> List[str]:
    """
    获取允许的模型列表
    
    Returns:
        模型列表
    """
    return list(_allowed_models) if _allowed_models else list(DEFAULT_ALLOWED_MODELS)


def reset_allowed_models() -> None:
    """重置允许列表为默认值"""
    global _allowed_models
    _allowed_models = []


# 导出
__all__ = [
    "DEFAULT_ALLOWED_MODELS",
    "is_model_allowed",
    "set_allowed_models",
    "get_allowed_models",
    "reset_allowed_models",
]
