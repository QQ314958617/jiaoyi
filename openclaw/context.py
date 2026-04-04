"""
Context - 上下文窗口管理
基于 Claude Code context.ts 设计

模型上下文窗口大小管理。
"""
import os


# 默认上下文窗口大小
MODEL_CONTEXT_WINDOW_DEFAULT = 200_000

# 紧凑操作的最大输出token
COMPACT_MAX_OUTPUT_TOKENS = 20_000

# 默认最大输出token
MAX_OUTPUT_TOKENS_DEFAULT = 32_000
MAX_OUTPUT_TOKENS_UPPER_LIMIT = 64_000

# 槽位优化的上限
CAPPED_DEFAULT_MAX_TOKENS = 8_000
ESCALATED_MAX_TOKENS = 64_000


def is_1m_context_disabled() -> bool:
    """
    检查1M上下文是否被禁用
    
    Returns:
        是否禁用
    """
    return os.environ.get('CLAUDE_CODE_DISABLE_1M_CONTEXT', '').lower() in ('1', 'true', 'yes')


def has_1m_context(model: str) -> bool:
    """
    检查模型是否支持1M上下文
    
    Args:
        model: 模型名
        
    Returns:
        是否支持1M
    """
    if is_1m_context_disabled():
        return False
    return '[1m]' in model.lower()


def model_supports_1m(model: str) -> bool:
    """
    检查模型是否支持1M上下文
    
    Args:
        model: 模型名
        
    Returns:
        是否支持
    """
    if is_1m_context_disabled():
        return False
    
    model_lower = model.lower()
    
    # 检查模型名称中的1M标记
    if '1m' in model_lower or '200k' in model_lower:
        return True
    
    # Sonnet 4和Opus 4.6默认支持
    if 'sonnet-4' in model_lower or 'opus-4-6' in model_lower:
        return True
    
    return False


def get_context_window_for_model(model: str) -> int:
    """
    获取模型的上下文窗口大小
    
    Args:
        model: 模型名
        
    Returns:
        上下文窗口大小
    """
    # 环境变量覆盖
    override = os.environ.get('CLAUDE_CODE_CONTEXT_WINDOW')
    if override:
        try:
            return int(override)
        except ValueError:
            pass
    
    # 1M模型
    if has_1m_context(model) or model_supports_1m(model):
        return 1_000_000
    
    # 默认200K
    return MODEL_CONTEXT_WINDOW_DEFAULT


def get_max_output_tokens(default: int = MAX_OUTPUT_TOKENS_DEFAULT) -> int:
    """
    获取最大输出token数
    
    Args:
        default: 默认值
        
    Returns:
        最大token数
    """
    # 环境变量覆盖
    override = os.environ.get('CLAUDE_CODE_MAX_OUTPUT_TOKENS')
    if override:
        try:
            value = int(override)
            return min(value, MAX_OUTPUT_TOKENS_UPPER_LIMIT)
        except ValueError:
            pass
    
    return default


# 导出
__all__ = [
    "MODEL_CONTEXT_WINDOW_DEFAULT",
    "COMPACT_MAX_OUTPUT_TOKENS",
    "MAX_OUTPUT_TOKENS_DEFAULT",
    "MAX_OUTPUT_TOKENS_UPPER_LIMIT",
    "CAPPED_DEFAULT_MAX_TOKENS",
    "ESCALATED_MAX_TOKENS",
    "is_1m_context_disabled",
    "has_1m_context",
    "model_supports_1m",
    "get_context_window_for_model",
    "get_max_output_tokens",
]
