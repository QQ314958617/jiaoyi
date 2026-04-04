"""
Slug - slug化
基于 Claude Code slug.ts 设计

URL slug工具。
"""
import re
import unicodedata


def slugify(text: str, max_length: int = None) -> str:
    """
    转为URL友好的slug
    
    Args:
        text: 文本
        max_length: 最大长度
        
    Returns:
        slug字符串
    """
    # Unicode NFKD规范化
    text = unicodedata.normalize('NFKD', text)
    
    # 移除重音符号
    text = ''.join(c for c in text if not unicodedata.combining(c))
    
    # 转小写
    text = text.lower()
    
    # 替换非字母数字为连字符
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    
    # 多个空格/连字符合并为一个
    text = re.sub(r'[\s-]+', '-', text)
    
    # 移除首尾连字符
    text = text.strip('-')
    
    if max_length:
        text = text[:max_length]
        text = text.rsplit('-', 1)[0]  # 不要截断单词
    
    return text


def slugify_chinese(text: str, max_length: int = None) -> str:
    """
    转为slug（保留中文字符）
    
    Args:
        text: 文本
        max_length: 最大长度
        
    Returns:
        slug字符串
    """
    # Unicode规范化
    text = unicodedata.normalize('NFKD', text)
    
    # 转小写
    text = text.lower()
    
    # 非字母数字、非中文、非连字符替换为-
    text = re.sub(r'[^\u4e00-\u9fa5a-z0-9-]', '-', text)
    
    # 多个连字符合并为一个
    text = re.sub(r'-+', '-', text)
    
    # 移除首尾连字符
    text = text.strip('-')
    
    if max_length:
        text = text[:max_length]
    
    return text


def is_valid_slug(slug: str) -> bool:
    """
    检查是否为有效slug
    
    Args:
        slug: slug字符串
        
    Returns:
        是否有效
    """
    if not slug:
        return False
    
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    return bool(re.match(pattern, slug))


def slug_to_title(slug: str) -> str:
    """
    slug转标题
    
    Args:
        slug: slug字符串
        
    Returns:
        标题字符串
    """
    return slug.replace('-', ' ').title()


# 导出
__all__ = [
    "slugify",
    "slugify_chinese",
    "is_valid_slug",
    "slug_to_title",
]
