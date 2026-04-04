"""
API Providers - API提供者管理
基于 Claude Code providers.ts 设计

管理不同的API提供者（firstParty/bedrock/vertex/foundry）。
"""
import os
from typing import Literal

from .env_utils import is_env_truthy


# API提供者类型
APIProvider = Literal['firstParty', 'bedrock', 'vertex', 'foundry']


def get_api_provider() -> APIProvider:
    """
    获取当前API提供者
    
    Returns:
        API提供者类型
    """
    if is_env_truthy(os.environ.get('CLAUDE_CODE_USE_BEDROCK')):
        return 'bedrock'
    if is_env_truthy(os.environ.get('CLAUDE_CODE_USE_VERTEX')):
        return 'vertex'
    if is_env_truthy(os.environ.get('CLAUDE_CODE_USE_FOUNDRY')):
        return 'foundry'
    return 'firstParty'


def is_first_party_anthropic_base_url() -> bool:
    """
    检查ANTHROPIC_BASE_URL是否为官方API URL
    
    Returns:
        是否为官方URL
    """
    base_url = os.environ.get('ANTHROPIC_BASE_URL')
    
    if not base_url:
        return True  # 默认使用官方API
    
    try:
        from urllib.parse import urlparse
        host = urlparse(base_url).netloc
        
        allowed_hosts = ['api.anthropic.com']
        
        # ANT用户还允许staging
        if os.environ.get('USER_TYPE') == 'ant':
            allowed_hosts.append('api-staging.anthropic.com')
        
        return host in allowed_hosts
        
    except Exception:
        return False


def get_api_base_url() -> str:
    """
    获取API基础URL
    
    Returns:
        API URL
    """
    return os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')


def get_api_key() -> str:
    """
    获取API密钥
    
    Returns:
        API密钥
    """
    return os.environ.get('ANTHROPIC_API_KEY', '')


# 导出
__all__ = [
    "APIProvider",
    "get_api_provider",
    "is_first_party_anthropic_base_url",
    "get_api_base_url",
    "get_api_key",
]
