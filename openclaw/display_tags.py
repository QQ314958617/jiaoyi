"""
Display Tags - 显示标签处理
基于 Claude Code displayTags.ts 设计

移除文本中的XML-like标签，用于UI标题显示。
"""
import re


# 匹配XML-like标签块（小写标签名）
XML_TAG_BLOCK_PATTERN = re.compile(
    r'<([a-z][\w-]*)(?:\s[^>]*)?>[\s\S]*?<\/\1>\n?',
    re.MULTILINE
)

# IDE上下文标签
IDE_CONTEXT_TAGS_PATTERN = re.compile(
    r'<(ide_opened_file|ide_selection)(?:\s[^>]*)?>[\s\S]*?<\/\1>\n?',
    re.MULTILINE
)


def strip_display_tags(text: str) -> str:
    """
    移除文本中的显示标签
    
    用于UI标题（/rewind, /resume, bridge session titles）。
    系统注入的上下文（IDE元数据、hook输出、任务通知）用标签包裹，
    不应该作为标题显示。
    
    Args:
        text: 原始文本
        
    Returns:
        移除标签后的文本
    """
    result = XML_TAG_BLOCK_PATTERN.sub('', text).strip()
    # 如果移除后为空，返回原始文本
    return result if result else text


def strip_display_tags_allow_empty(text: str) -> str:
    """
    移除显示标签，允许空结果
    
    当所有内容都是标签时返回空字符串。
    用于检测纯命令提示（如/clear）。
    
    Args:
        text: 原始文本
        
    Returns:
        移除标签后的文本（可能为空）
    """
    return XML_TAG_BLOCK_PATTERN.sub('', text).strip()


def strip_ide_context_tags(text: str) -> str:
    """
    只移除IDE注入的上下文标签
    
    用于textForResubmit，保留用户输入但移除IDE噪音。
    
    Args:
        text: 原始文本
        
    Returns:
        移除IDE标签后的文本
    """
    return IDE_CONTEXT_TAGS_PATTERN.sub('', text).strip()


def extract_display_tags(text: str) -> list[str]:
    """
    提取文本中的所有标签
    
    Args:
        text: 原始文本
        
    Returns:
        标签列表
    """
    matches = XML_TAG_BLOCK_PATTERN.findall(text)
    return list(set(matches))


# 导出
__all__ = [
    "strip_display_tags",
    "strip_display_tags_allow_empty",
    "strip_ide_context_tags",
    "extract_display_tags",
    "XML_TAG_BLOCK_PATTERN",
    "IDE_CONTEXT_TAGS_PATTERN",
]
