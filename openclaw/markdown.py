"""
Markdown - Markdown解析
基于 Claude Code markdown.ts 设计

Markdown工具。
"""
import re
from typing import List, Dict


def extract_headers(text: str) -> List[Dict[str, str]]:
    """
    提取标题
    
    Returns:
        [{"level": 1, "text": "Title"}]
    """
    pattern = r'^(#{1,6})\s+(.+)$'
    headers = []
    
    for line in text.splitlines():
        match = re.match(pattern, line.strip())
        if match:
            headers.append({
                "level": len(match.group(1)),
                "text": match.group(2).strip()
            })
    
    return headers


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    提取代码块
    
    Returns:
        [{"lang": "python", "code": "..."}]
    """
    pattern = r'```(\w*)\n(.*?)```'
    blocks = []
    
    for match in re.finditer(pattern, text, re.DOTALL):
        blocks.append({
            "lang": match.group(1) or "",
            "code": match.group(2).strip()
        })
    
    return blocks


def extract_links(text: str) -> List[Dict[str, str]]:
    """
    提取链接
    
    Returns:
        [{"text": "...", "url": "..."}]
    """
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    links = []
    
    for match in re.finditer(pattern, text):
        links.append({
            "text": match.group(1),
            "url": match.group(2)
        })
    
    return links


def extract_images(text: str) -> List[Dict[str, str]]:
    """
    提取图片
    
    Returns:
        [{"alt": "...", "url": "..."}]
    """
    pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    images = []
    
    for match in re.finditer(pattern, text):
        images.append({
            "alt": match.group(1),
            "url": match.group(2)
        })
    
    return images


def strip_markdown(text: str) -> str:
    """
    移除markdown格式
    """
    # 移除代码块
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    
    # 移除行内代码
    text = re.sub(r'`[^`]+`', '', text)
    
    # 移除图片
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    
    # 移除链接
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 移除标题标记
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # 移除加粗斜体
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    
    # 移除引用
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # 移除列表标记
    text = re.sub(r'^[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    return text.strip()


def to_html(text: str) -> str:
    """
    简单Markdown转HTML
    """
    html = text
    
    # 转义HTML
    html = html.replace('&', '&amp;')
    html = html.replace('<', '&lt;')
    html = html.replace('>', '&gt;')
    
    # 代码块
    html = re.sub(r'```(\w*)\n(.*?)```', 
                  r'<pre><code class="\1">\2</code></pre>', 
                  html, flags=re.DOTALL)
    
    # 行内代码
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # 标题
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # 加粗
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # 斜体
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # 链接
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', 
                  r'<a href="\2">\1</a>', html)
    
    # 换行
    html = html.replace('\n\n', '</p><p>')
    html = '<p>' + html + '</p>'
    
    return html


# 导出
__all__ = [
    "extract_headers",
    "extract_code_blocks",
    "extract_links",
    "extract_images",
    "strip_markdown",
    "to_html",
]
