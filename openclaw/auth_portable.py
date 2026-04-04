"""
Auth Portable - 便携认证
基于 Claude Code authPortable.ts 设计

跨平台的API Key认证管理。
"""
import os
import re
from typing import Optional


def normalize_api_key_for_config(api_key: str) -> str:
    """
    规范化API Key用于配置
    
    Args:
        api_key: 原始API Key
        
    Returns:
        规范化后的Key
    """
    if not api_key:
        return ''
    
    # 移除空白
    api_key = api_key.strip()
    
    # 移除前缀
    prefixes_to_remove = ['sk-', 'sk-ant-']
    for prefix in prefixes_to_remove:
        if api_key.startswith(prefix):
            api_key = api_key[len(prefix):]
    
    return api_key


def is_valid_api_key(api_key: str) -> bool:
    """
    检查API Key是否有效
    
    Args:
        api_key: API Key
        
    Returns:
        是否有效
    """
    if not api_key:
        return False
    
    # 移除空白和前缀
    normalized = normalize_api_key_for_config(api_key)
    
    # 检查长度（sk-ant-api开头通常是44-48字符）
    if len(normalized) < 40:
        return False
    
    # 检查是否只包含有效字符
    if not re.match(r'^[a-zA-Z0-9_-]+$', normalized):
        return False
    
    return True


def mask_api_key(api_key: str) -> str:
    """
    遮蔽API Key用于显示
    
    Args:
        api_key: 完整API Key
        
    Returns:
        遮蔽后的Key
    """
    if not api_key:
        return ''
    
    normalized = normalize_api_key_for_config(api_key)
    
    if len(normalized) <= 8:
        return '***'
    
    # 显示前4后4
    return f"{normalized[:4]}...{normalized[-4:]}"


# 导出
__all__ = [
    "normalize_api_key_for_config",
    "is_valid_api_key",
    "mask_api_key",
]
