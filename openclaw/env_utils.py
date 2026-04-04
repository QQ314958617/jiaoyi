"""
Environment Utilities - 环境变量工具
基于 Claude Code envUtils.ts 设计

提供环境变量读取和解析的便捷函数。
"""
import os
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=1)
def get_claude_config_home_dir() -> str:
    """
    获取Claude配置目录
    
    Returns:
        配置目录路径（默认~/.claude）
    """
    config_dir = os.environ.get('CLAUDE_CONFIG_DIR')
    if config_dir:
        return os.path.normpath(os.path.expanduser(config_dir))
    return os.path.normpath(os.path.join(os.path.expanduser('~'), '.claude'))


def get_teams_dir() -> str:
    """
    获取Teams目录
    
    Returns:
        teams目录路径
    """
    return os.path.join(get_claude_config_home_dir(), 'teams')


def is_env_truthy(value: Optional[str | bool]) -> bool:
    """
    检查环境变量是否为真值
    
    Args:
        value: 环境变量值
        
    Returns:
        是否为真
    """
    if not value:
        return False
    if isinstance(value, bool):
        return value
    normalized = str(value).lower().strip()
    return normalized in ('1', 'true', 'yes', 'on')


def is_env_defined_falsy(value: Optional[str | bool]) -> bool:
    """
    检查环境变量是否明确设置为假值
    
    Args:
        value: 环境变量值
        
    Returns:
        是否明确设置为假
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return not value
    if not value:
        return False
    normalized = str(value).lower().strip()
    return normalized in ('0', 'false', 'no', 'off')


def is_bare_mode() -> bool:
    """
    检查是否为bare模式（--bare）
    
    Returns:
        是否为bare模式
    """
    return (
        is_env_truthy(os.environ.get('CLAUDE_CODE_SIMPLE')) or
        '--bare' in os.sys.argv
    )


def parse_env_vars(
    raw_env_args: Optional[list[str]] = None,
) -> dict[str, str]:
    """
    解析环境变量数组
    
    Args:
        raw_env_args: KEY=VALUE格式的字符串数组
        
    Returns:
        键值对字典
    """
    parsed: dict[str, str] = {}
    
    if not raw_env_args:
        return parsed
    
    for env_str in raw_env_args:
        if '=' not in env_str:
            raise ValueError(
                f"Invalid environment variable format: {env_str}, "
                "environment variables should be added as: -e KEY1=value1 -e KEY2=value2"
            )
        
        key, *value_parts = env_str.split('=', 1)
        if not key:
            raise ValueError(f"Invalid environment variable format: {env_str}")
        
        parsed[key] = '='.join(value_parts)
    
    return parsed


def get_aws_region() -> str:
    """
    获取AWS区域
    
    Returns:
        AWS区域
    """
    return os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION') or 'us-east-1'


def get_vertex_region_for_model(model: Optional[str] = None) -> Optional[str]:
    """
    获取模型的Vertex AI区域
    
    Args:
        model: 模型名称
        
    Returns:
        区域或None
    """
    if not model:
        return None
    
    # 模型前缀到环境变量的映射
    vertex_overrides: list[tuple[str, str]] = [
        ('claude-haiku-4-5', 'VERTEX_REGION_CLAUDE_HAIKU_4_5'),
        ('claude-3-5-haiku', 'VERTEX_REGION_CLAUDE_3_5_HAIKU'),
        ('claude-3-5-sonnet', 'VERTEX_REGION_CLAUDE_3_5_SONNET'),
        ('claude-3-7-sonnet', 'VERTEX_REGION_CLAUDE_3_7_SONNET'),
        ('claude-opus-4-1', 'VERTEX_REGION_CLAUDE_4_1_OPUS'),
        ('claude-opus-4', 'VERTEX_REGION_CLAUDE_4_0_OPUS'),
        ('claude-sonnet-4-6', 'VERTEX_REGION_CLAUDE_4_6_SONNET'),
        ('claude-sonnet-4-5', 'VERTEX_REGION_CLAUDE_4_5_SONNET'),
        ('claude-sonnet-4', 'VERTEX_REGION_CLAUDE_4_0_SONNET'),
    ]
    
    for prefix, env_var in vertex_overrides:
        if model.startswith(prefix):
            return os.environ.get(env_var)
    
    return None


# 导出
__all__ = [
    "get_claude_config_home_dir",
    "get_teams_dir",
    "is_env_truthy",
    "is_env_defined_falsy",
    "is_bare_mode",
    "parse_env_vars",
    "get_aws_region",
    "get_vertex_region_for_model",
]
