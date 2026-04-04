"""
Claude Memory - 记忆文件加载
基于 Claude Code claudemd.ts 设计（简化版）

加载和管理CLAUDE.md记忆文件。
"""
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set


class MemoryType(Enum):
    """记忆文件类型"""
    MANAGED = "Managed"
    USER = "User"
    PROJECT = "Project"
    LOCAL = "Local"
    AUTOMEM = "AutoMem"
    TEAMMEM = "TeamMem"


@dataclass
class MemoryFileInfo:
    """记忆文件信息"""
    path: str
    type: MemoryType
    content: str
    parent: Optional[str] = None
    globs: Optional[List[str]] = None
    content_differs_from_disk: bool = False
    raw_content: Optional[str] = None


# 允许的文件扩展名
TEXT_FILE_EXTENSIONS = {
    '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.xml', '.csv',
    '.html', '.htm', '.css', '.js', '.ts', '.tsx', '.jsx', '.py', '.pyi',
    '.rb', '.go', '.rs', '.java', '.kt', '.cs', '.swift', '.sh', '.bash',
    '.sql', '.graphql', '.env', '.ini', '.cfg', '.conf',
}

MAX_MEMORY_CHARACTER_COUNT = 40000
MAX_INCLUDE_DEPTH = 5


def is_text_file(file_path: str) -> bool:
    """
    检查是否为文本文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为文本文件
    """
    import os
    ext = os.path.splitext(file_path)[1].lower()
    return ext in TEXT_FILE_EXTENSIONS


def parse_frontmatter(content: str) -> dict:
    """
    解析frontmatter
    
    Args:
        content: 文件内容
        
    Returns:
        {"frontmatter": dict, "content": str}
    """
    if not content.startswith('---'):
        return {"frontmatter": {}, "content": content}
    
    end_match = re.search(r'^---$', content[3:], re.MULTILINE)
    if not end_match:
        return {"frontmatter": {}, "content": content}
    
    end_pos = end_match.start() + 3
    fm_content = content[3:end_pos].strip()
    body = content[end_pos + 3:].strip()
    
    frontmatter = {}
    for line in fm_content.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            frontmatter[key.strip()] = value.strip()
    
    return {"frontmatter": frontmatter, "content": body}


def strip_html_comments(content: str) -> str:
    """
    移除HTML注释
    
    Args:
        content: 内容
        
    Returns:
        移除注释后的内容
    """
    # 移除块级HTML注释
    pattern = re.compile(r'<!--[\s\S]*?-->', re.MULTILINE)
    return pattern.sub('', content)


def extract_include_paths(content: str, base_path: str) -> List[str]:
    """
    从内容中提取@include路径
    
    Args:
        content: 文件内容
        base_path: 基础路径
        
    Returns:
        包含的文件路径列表
    """
    paths = []
    # 匹配@path, @./path, @~/path, @/path
    pattern = re.compile(r'(?:^|\s)@((?:[^\s\\]|\\ )+)')
    
    for match in pattern.finditer(content):
        path = match.group(1)
        if not path:
            continue
        
        # 移除fragment
        if '#' in path:
            path = path.split('#')[0]
        
        # 展开路径
        if path.startswith('~/'):
            path = os.path.expanduser(path)
        elif path.startswith('./'):
            path = os.path.join(os.path.dirname(base_path), path[2:])
        elif not path.startswith('/'):
            path = os.path.join(os.path.dirname(base_path), path)
        
        paths.append(path)
    
    return paths


def truncate_content(content: str, max_chars: int = MAX_MEMORY_CHARACTER_COUNT) -> str:
    """
    截断内容到最大字符数
    
    Args:
        content: 内容
        max_chars: 最大字符数
        
    Returns:
        截断后的内容
    """
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + f"\n\n[Truncated {len(content) - max_chars} characters]"


def get_memory_file_info(file_path: str, memory_type: MemoryType) -> Optional[MemoryFileInfo]:
    """
    获取记忆文件信息
    
    Args:
        file_path: 文件路径
        memory_type: 记忆类型
        
    Returns:
        MemoryFileInfo或None
    """
    if not os.path.exists(file_path):
        return None
    
    if not is_text_file(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
    except Exception:
        return None
    
    # 解析frontmatter
    parsed = parse_frontmatter(raw_content)
    frontmatter = parsed['frontmatter']
    content = parsed['content']
    
    # 移除HTML注释
    content = strip_html_comments(content)
    
    # 截断
    if memory_type in (MemoryType.AUTOMEM, MemoryType.TEAMMEM):
        content = truncate_content(content)
    
    # 检查是否与磁盘内容不同
    content_differs = content != raw_content
    
    return MemoryFileInfo(
        path=file_path,
        type=memory_type,
        content=content,
        parent=None,
        globs=frontmatter.get('paths', '').split() if 'paths' in frontmatter else None,
        content_differs_from_disk=content_differs,
        raw_content=raw_content if content_differs else None,
    )


def get_claude_md_paths(cwd: str) -> dict:
    """
    获取CLAUDE.md文件的可能路径
    
    Args:
        cwd: 当前工作目录
        
    Returns:
        各种CLAUDE.md路径字典
    """
    home = os.path.expanduser('~')
    
    paths = {
        'managed': '/etc/claude-code/CLAUDE.md',
        'user': os.path.join(home, '.claude', 'CLAUDE.md'),
        'project': [],
        'local': [],
    }
    
    # 从CWD向上遍历找项目文件
    current = cwd
    while True:
        # CLAUDE.md
        paths['project'].append(os.path.join(current, 'CLAUDE.md'))
        paths['project'].append(os.path.join(current, '.claude', 'CLAUDE.md'))
        
        # CLAUDE.local.md
        paths['local'].append(os.path.join(current, 'CLAUDE.local.md'))
        
        parent = os.path.dirname(current)
        if parent == current:  # 到达根目录
            break
        current = parent
    
    return paths


# 导出
__all__ = [
    "MemoryType",
    "MemoryFileInfo",
    "TEXT_FILE_EXTENSIONS",
    "MAX_MEMORY_CHARACTER_COUNT",
    "is_text_file",
    "parse_frontmatter",
    "strip_html_comments",
    "extract_include_paths",
    "truncate_content",
    "get_memory_file_info",
    "get_claude_md_paths",
]
