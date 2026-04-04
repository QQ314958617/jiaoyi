"""
Agent Swarms Enabled - Agent团队功能开关
基于 Claude Code agentSwarmsEnabled.ts 设计

集中管理Agent团队功能的运行时开关。
"""
import os
import sys


def _is_agent_teams_flag_set() -> bool:
    """
    检查是否设置了--agent-teams标志
    
    Returns:
        是否设置了标志
    """
    return '--agent-teams' in sys.argv


def is_agent_swarms_enabled() -> bool:
    """
    检查Agent团队功能是否启用
    
    内部版本：始终启用
    外部版本需要：
    1. CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS环境变量或--agent-teams标志
    2. GrowthBook开关'tengu_amber_flint'启用
    
    Returns:
        是否启用
    """
    # 内部版本：始终启用
    if os.environ.get('USER_TYPE') == 'ant':
        return True
    
    # 外部版本：需要显式启用
    env_enabled = os.environ.get('CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS', '').lower()
    flag_enabled = _is_agent_teams_flag_set()
    
    if not env_enabled and not flag_enabled:
        return False
    
    # 注意：GrowthBook检查在Python中简化处理
    # 实际实现中应该调用GrowthBook SDK
    # 这里假设总是启用（除非killswitch关闭）
    killswitch_enabled = True  # 简化
    
    return killswitch_enabled


def is_agent_teams_flag_set() -> bool:
    """检查是否设置了--agent-teams标志"""
    return _is_agent_teams_flag_set()


# 导出
__all__ = [
    "is_agent_swarms_enabled",
    "is_agent_teams_flag_set",
]
