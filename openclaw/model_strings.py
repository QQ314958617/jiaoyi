"""
Model Strings - 模型字符串
基于 Claude Code modelStrings.ts 设计

模型名称和别名管理。
"""
from typing import Dict, Optional


# 模型别名映射
MODEL_ALIASES: Dict[str, str] = {
    'haiku': 'claude-haiku-4-6-20251120',
    'sonnet': 'claude-sonnet-4-6-20251120',
    'opus': 'claude-opus-4-6-20251120',
    'opus4': 'claude-opus-4-6-20251120',
    'sonnet4': 'claude-sonnet-4-6-20251120',
    'haiku4': 'claude-haiku-4-6-20251120',
}


def get_model_alias(alias: str) -> Optional[str]:
    """
    获取模型的别名
    
    Args:
        alias: 别名
        
    Returns:
        完整模型名或None
    """
    return MODEL_ALIASES.get(alias.lower())


def is_model_alias(name: str) -> bool:
    """
    检查是否为模型别名
    
    Args:
        name: 名称
        
    Returns:
        是否为别名
    """
    return name.lower() in MODEL_ALIASES


def resolve_model(model: str) -> str:
    """
    解析模型名称或别名
    
    Args:
        model: 模型名或别名
        
    Returns:
        完整模型名
    """
    return MODEL_ALIASES.get(model.lower(), model)


def get_model_strings() -> Dict[str, str]:
    """
    获取模型字符串映射
    
    Returns:
        别名到完整名称的映射
    """
    return dict(MODEL_ALIASES)


def is_opus_model(model: str) -> bool:
    """
    检查是否为Opus模型
    
    Args:
        model: 模型名
        
    Returns:
        是否为Opus
    """
    return 'opus' in model.lower()


def is_sonnet_model(model: str) -> bool:
    """
    检查是否为Sonnet模型
    
    Args:
        model: 模型名
        
    Returns:
        是否为Sonnet
    """
    return 'sonnet' in model.lower()


def is_haiku_model(model: str) -> bool:
    """
    检查是否为Haiku模型
    
    Args:
        model: 模型名
        
    Returns:
        是否为Haiku
    """
    return 'haiku' in model.lower()


# 导出
__all__ = [
    "MODEL_ALIASES",
    "get_model_alias",
    "is_model_alias",
    "resolve_model",
    "get_model_strings",
    "is_opus_model",
    "is_sonnet_model",
    "is_haiku_model",
]
