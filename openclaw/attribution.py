"""
Attribution - 归属文本生成
基于 Claude Code attribution.ts 设计

生成git commit和PR的归属信息。
"""
import os


PRODUCT_URL = "https://www.claude.ai/code"


def get_attribution_texts(
    model: str = "claude-opus-4-5",
    settings: dict = None,
) -> dict:
    """
    获取归属文本
    
    Args:
        model: 模型名称
        settings: 设置
        
    Returns:
        {"commit": str, "pr": str}
    """
    settings = settings or {}
    
    # 默认归属
    default_commit = f"Co-Authored-By: {model} <noreply@anthropic.com>"
    default_pr = f"🤖 Generated with [Claude Code]({PRODUCT_URL})"
    
    # 检查是否有自定义归属设置
    if settings.get("attribution"):
        attr = settings["attribution"]
        return {
            "commit": attr.get("commit", default_commit),
            "pr": attr.get("pr", default_pr),
        }
    
    # 检查是否禁用了co-authored
    if settings.get("includeCoAuthoredBy") is False:
        return {"commit": "", "pr": ""}
    
    return {"commit": default_commit, "pr": default_pr}


def get_enhanced_pr_attribution(
    model: str,
    claude_percent: int = 0,
    prompt_count: int = 0,
    memory_access_count: int = 0,
    is_internal: bool = False,
) -> str:
    """
    获取增强的PR归属文本
    
    格式: "🤖 Generated with Claude Code (93% 3-shotted by claude-opus-4-5, 2 memories recalled)"
    
    Args:
        model: 模型名称
        claude_percent: Claude贡献百分比
        prompt_count: 提示次数
        memory_access_count: 记忆访问次数
        is_internal: 是否为内部仓库
        
    Returns:
        增强的PR归属文本
    """
    default_attr = f"🤖 Generated with [Claude Code]({PRODUCT_URL})"
    
    # 如果没有数据，返回默认
    if claude_percent == 0 and prompt_count == 0 and memory_access_count == 0:
        return default_attr
    
    # 构建记忆后缀
    mem_suffix = ""
    if memory_access_count > 0:
        mem_word = "memory" if memory_access_count == 1 else "memories"
        mem_suffix = f", {memory_access_count} {mem_word} recalled"
    
    # 构建N-shot后缀
    shot_suffix = f" {prompt_count}-shotted by {model}"
    
    # 构建完整归属
    return f"🤖 Generated with [Claude Code]({PRODUCT_URL}) ({claude_percent}%{shot_suffix}{mem_suffix})"


def is_terminal_output(content: str) -> bool:
    """
    检查内容是否为终端输出
    
    Args:
        content: 内容
        
    Returns:
        是否为终端输出
    """
    terminal_tags = [
        "bash_input",
        "bash_output",
        "terminal_output",
    ]
    
    for tag in terminal_tags:
        if f"<{tag}>" in content:
            return True
    
    return False


def count_user_prompts(messages: list) -> int:
    """
    统计用户消息数量
    
    Args:
        messages: 消息列表
        
    Returns:
        用户消息数量
    """
    count = 0
    
    for msg in messages:
        if msg.get("type") != "user":
            continue
        
        content = msg.get("message", {}).get("content", "")
        if not content:
            continue
        
        if isinstance(content, str):
            if is_terminal_output(content):
                continue
            if content.strip():
                count += 1
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text = block.get("text", "")
                        if text and not is_terminal_output(text):
                            count += 1
                            break
                    elif block.get("type") in ("image", "document"):
                        count += 1
                        break
    
    return count


# 导出
__all__ = [
    "PRODUCT_URL",
    "get_attribution_texts",
    "get_enhanced_pr_attribution",
    "is_terminal_output",
    "count_user_prompts",
]
