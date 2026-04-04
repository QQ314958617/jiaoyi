"""
Tokens - Token计算工具
基于 Claude Code tokens.ts 设计

Token使用量计算。
"""
from typing import Any, Dict, List, Optional


def get_token_count_from_usage(usage: Dict[str, int]) -> int:
    """
    从usage计算总token数
    
    Args:
        usage: API使用量
        
    Returns:
        总token数
    """
    return (
        usage.get('input_tokens', 0) +
        usage.get('cache_creation_input_tokens', 0) +
        usage.get('cache_read_input_tokens', 0) +
        usage.get('output_tokens', 0)
    )


def estimate_token_count(text: str) -> int:
    """
    估算文本的token数
    
    简化估算：中文约1.5字符/token，英文约4字符/token。
    
    Args:
        text: 文本
        
    Returns:
        估算token数
    """
    if not text:
        return 0
    
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    
    return int(chinese_chars / 1.5 + other_chars / 4)


def estimate_messages_token_count(messages: List[Dict]) -> int:
    """
    估算消息列表的token数
    
    Args:
        messages: 消息列表
        
    Returns:
        估算token数
    """
    total = 0
    
    for msg in messages:
        msg_type = msg.get('type', '')
        
        # 角色标记
        total += 4  # 约4 token的角色标记
        
        # 内容
        content = msg.get('message', {}).get('content', '')
        if isinstance(content, str):
            total += estimate_token_count(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get('type') == 'text':
                        total += estimate_token_count(block.get('text', ''))
                    elif block.get('type') == 'tool_use':
                        # 工具调用
                        total += estimate_token_count(str(block))
                    elif block.get('type') == 'tool_result':
                        total += estimate_token_count(str(block))
    
    return total


def rough_token_count_estimation_for_messages(messages: List[Dict]) -> int:
    """
    消息的粗略token估算
    
    Args:
        messages: 消息列表
        
    Returns:
        估算token数
    """
    return estimate_messages_token_count(messages)


def does_context_exceed_threshold(
    messages: List[Dict],
    threshold: int = 200000,
) -> bool:
    """
    检查上下文是否超过阈值
    
    Args:
        messages: 消息列表
        threshold: 阈值
        
    Returns:
        是否超过
    """
    # 查找最后一条有usage的assistant消息
    for msg in reversed(messages):
        if msg.get('type') == 'assistant':
            usage = msg.get('message', {}).get('usage')
            if usage:
                return get_token_count_from_usage(usage) > threshold
    
    # 没有usage，使用估算
    return rough_token_count_estimation_for_messages(messages) > threshold


def get_assistant_message_content_length(message: Dict) -> int:
    """
    获取assistant消息内容长度
    
    Args:
        message: 消息
        
    Returns:
        内容长度
    """
    content_length = 0
    content = message.get('message', {}).get('content', [])
    
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                block_type = block.get('type')
                if block_type == 'text':
                    content_length += len(block.get('text', ''))
                elif block_type == 'thinking':
                    content_length += len(block.get('thinking', ''))
                elif block_type == 'redacted_thinking':
                    content_length += len(block.get('data', ''))
                elif block_type == 'tool_use':
                    import json
                    content_length += len(json.dumps(block.get('input', {})))
    
    return content_length


# 导出
__all__ = [
    "get_token_count_from_usage",
    "estimate_token_count",
    "estimate_messages_token_count",
    "rough_token_count_estimation_for_messages",
    "does_context_exceed_threshold",
    "get_assistant_message_content_length",
]
