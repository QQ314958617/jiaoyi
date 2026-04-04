"""
Betas - 模型Beta特性管理
基于 Claude Code betas.ts 设计

管理模型的Beta特性和API headers。
"""
from typing import Optional
from functools import lru_cache


# Beta Header 常量
CONTEXT_1M_BETA = "context-1m"
CONTEXT_1M_COMPUTE_BETA = "context-1m-compute"
INTERLEAVED_THINKING_BETA = "interleaved-thinking"
PROMPT_CACHING_BETA = "prompt-caching-2025-05-14"
WEB_SEARCH_BETA = "web-search-2025-05-14"


class BetaManager:
    """
    Beta特性管理器
    
    管理模型支持的Beta特性和headers。
    """
    
    def __init__(self):
        self._model_betas_cache = {}
        self._sdk_betas = []
    
    def set_sdk_betas(self, betas: list[str]) -> None:
        """设置SDK提供的betas"""
        self._sdk_betas = betas
    
    def get_model_betas(self, model: str) -> list[str]:
        """
        获取模型支持的Beta headers
        
        Args:
            model: 模型名称
            
        Returns:
            Beta headers列表
        """
        if model in self._model_betas_cache:
            return self._model_betas_cache[model]
        
        betas = self._compute_model_betas(model)
        self._model_betas_cache[model] = betas
        return betas
    
    def _compute_model_betas(self, model: str) -> list[str]:
        """计算模型应使用的Beta headers"""
        betas = []
        model_lower = model.lower()
        
        # Haiku模型不支持某些特性
        is_haiku = 'haiku' in model_lower
        
        # Claude 4系列模型支持更多特性
        is_claude_4 = any(x in model_lower for x in ['opus-4', 'sonnet-4', 'haiku-4'])
        
        # Context 1M支持
        if '1m' in model or '200k' in model:
            betas.append(CONTEXT_1M_BETA)
        
        # Interleaved thinking
        if not is_haiku and is_claude_4:
            betas.append(INTERLEAVED_THINKING_BETA)
        
        # Prompt caching
        if is_claude_4:
            betas.append(PROMPT_CACHING_BETA)
        
        return betas
    
    def get_merged_betas(
        self,
        model: str,
        is_agentic: bool = False,
    ) -> list[str]:
        """
        合并SDK betas和模型betas
        
        Args:
            model: 模型名称
            is_agentic: 是否为agentic查询
            
        Returns:
            合并后的betas列表
        """
        base_betas = self.get_model_betas(model)
        
        # Agentic查询总是需要特定的betas
        if is_agentic and 'claude-code' not in str(self._sdk_betas):
            if 'claude-code-20250219' not in base_betas:
                base_betas = [f"claude-code-20250219"] + base_betas
        
        # 合并SDK betas
        if self._sdk_betas:
            for beta in self._sdk_betas:
                if beta not in base_betas:
                    base_betas.append(beta)
        
        return base_betas
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._model_betas_cache.clear()


# 全局Beta管理器
_beta_manager: Optional[BetaManager] = None


def get_beta_manager() -> BetaManager:
    """获取全局Beta管理器"""
    global _beta_manager
    if _beta_manager is None:
        _beta_manager = BetaManager()
    return _beta_manager


def model_supports_context_management(model: str) -> bool:
    """
    检查模型是否支持上下文管理
    
    Args:
        model: 模型名称
        
    Returns:
        是否支持
    """
    model_lower = model.lower()
    return (
        'opus-4' in model_lower or
        'sonnet-4' in model_lower or
        'haiku-4' in model_lower
    )


def model_supports_structured_outputs(model: str) -> bool:
    """
    检查模型是否支持结构化输出
    
    Args:
        model: 模型名称
        
    Returns:
        是否支持
    """
    model_lower = model.lower()
    # 目前只支持部分模型
    return (
        'sonnet-4-5' in model_lower or
        'sonnet-4-6' in model_lower or
        'opus-4-5' in model_lower or
        'opus-4-6' in model_lower or
        'haiku-4-5' in model_lower
    )


def model_supports_web_search(model: str) -> bool:
    """
    检查模型是否支持网络搜索
    
    Args:
        model: 模型名称
        
    Returns:
        是否支持
    """
    model_lower = model.lower()
    return (
        'opus-4' in model_lower or
        'sonnet-4' in model_lower or
        'haiku-4' in model_lower
    )


# 导出
__all__ = [
    "BetaManager",
    "get_beta_manager",
    "model_supports_context_management",
    "model_supports_structured_outputs",
    "model_supports_web_search",
    "CONTEXT_1M_BETA",
    "INTERLEAVED_THINKING_BETA",
    "PROMPT_CACHING_BETA",
    "WEB_SEARCH_BETA",
]
