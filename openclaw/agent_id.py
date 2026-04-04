"""
Agent ID - Agent标识系统
基于 Claude Code agentId.ts 设计

提供Agent ID的格式化和解析。
"""
from typing import Optional


def format_agent_id(agent_name: str, team_name: str) -> str:
    """
    格式化Agent ID
    
    格式: `agentName@teamName`
    
    Args:
        agent_name: Agent名称
        team_name: 团队名称
        
    Returns:
        Agent ID
    """
    return f"{agent_name}@{team_name}"


def parse_agent_id(
    agent_id: str,
) -> Optional[dict]:
    """
    解析Agent ID
    
    Args:
        agent_id: Agent ID
        
    Returns:
        {"agentName": str, "teamName": str} 或 None
    """
    if '@' not in agent_id:
        return None
    
    parts = agent_id.split('@', 1)
    if len(parts) != 2:
        return None
    
    return {
        "agentName": parts[0],
        "teamName": parts[1],
    }


def generate_request_id(request_type: str, agent_id: str) -> str:
    """
    生成请求ID
    
    格式: `{requestType}-{timestamp}@{agentId}`
    
    Args:
        request_type: 请求类型
        agent_id: Agent ID
        
    Returns:
        请求ID
    """
    import time
    timestamp = int(time.time() * 1000)
    return f"{request_type}-{timestamp}@{agent_id}"


def parse_request_id(
    request_id: str,
) -> Optional[dict]:
    """
    解析请求ID
    
    Args:
        request_id: 请求ID
        
    Returns:
        {"requestType": str, "timestamp": int, "agentId": str} 或 None
    """
    if '@' not in request_id:
        return None
    
    at_index = request_id.index('@')
    prefix = request_id[:at_index]
    agent_id = request_id[at_index + 1:]
    
    # 找到最后一个-的位置（时间戳在最后）
    last_dash_index = prefix.rfind('-')
    if last_dash_index == -1:
        return None
    
    request_type = prefix[:last_dash_index]
    timestamp_str = prefix[last_dash_index + 1:]
    
    try:
        timestamp = int(timestamp_str)
    except ValueError:
        return None
    
    return {
        "requestType": request_type,
        "timestamp": timestamp,
        "agentId": agent_id,
    }


# 导出
__all__ = [
    "format_agent_id",
    "parse_agent_id",
    "generate_request_id",
    "parse_request_id",
]
