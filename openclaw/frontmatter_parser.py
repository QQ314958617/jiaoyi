"""
Frontmatter Parser - Frontmatter解析器
基于 Claude Code frontmatterParser.ts 设计

解析markdown文件中的YAML frontmatter。
"""
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FrontmatterData:
    """Frontmatter数据"""
    allowed_tools: Optional[List[str]] = None
    description: Optional[str] = None
    type: Optional[str] = None
    argument_hint: Optional[str] = None
    when_to_use: Optional[str] = None
    version: Optional[str] = None
    hide_from_slash_command_tool: Optional[bool] = None
    model: Optional[str] = None
    skills: Optional[List[str]] = None
    user_invocable: Optional[bool] = None
    hooks: Optional[Dict] = None
    effort: Optional[str] = None
    context: Optional[str] = None
    agent: Optional[str] = None
    paths: Optional[List[str]] = None
    shell: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "FrontmatterData":
        """从字典创建"""
        return cls(
            allowed_tools=data.get('allowed-tools'),
            description=data.get('description'),
            type=data.get('type'),
            argument_hint=data.get('argument-hint'),
            when_to_use=data.get('when_to_use'),
            version=data.get('version'),
            hide_from_slash_command_tool=data.get('hide-from-slash-command-tool'),
            model=data.get('model'),
            skills=data.get('skills'),
            user_invocable=data.get('user-invocable'),
            hooks=data.get('hooks'),
            effort=data.get('effort'),
            context=data.get('context'),
            agent=data.get('agent'),
            paths=data.get('paths'),
            shell=data.get('shell'),
        )


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    解析frontmatter
    
    Args:
        content: 文件内容
        
    Returns:
        (frontmatter字典, 正文内容)
    """
    if not content.startswith('---'):
        return {}, content
    
    # 找到结束标记
    end_match = re.search(r'^---$', content[3:], re.MULTILINE)
    if not end_match:
        return {}, content
    
    end_pos = end_match.start() + 3
    fm_content = content[3:end_pos].strip()
    body = content[end_pos + 3:].strip()
    
    # 解析YAML（简化实现）
    frontmatter = _parse_yaml_simple(fm_content)
    
    return frontmatter, body


def _parse_yaml_simple(yaml_str: str) -> Dict[str, Any]:
    """
    简化YAML解析
    
    支持基本类型和简单结构。
    
    Args:
        yaml_str: YAML字符串
        
    Returns:
        解析后的字典
    """
    result = {}
    current_key = None
    current_list = []
    in_list = False
    
    for line in yaml_str.split('\n'):
        stripped = line.strip()
        
        # 空行
        if not stripped:
            if in_list:
                if current_key and current_list:
                    result[current_key] = current_list
                current_key = None
                current_list = []
                in_list = False
            continue
        
        # 列表项
        if stripped.startswith('- '):
            in_list = True
            value = stripped[2:].strip()
            current_list.append(_parse_value(value))
            continue
        
        # 键值对
        if ':' in stripped and not stripped.startswith('#'):
            # 保存之前的列表
            if in_list and current_key:
                result[current_key] = current_list
                current_key = None
                current_list = []
                in_list = False
            
            key, value = stripped.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if value:
                result[key] = _parse_value(value)
            else:
                current_key = key
                current_list = []
                in_list = False
        
        # 注释
        elif stripped.startswith('#'):
            continue
    
    # 保存最后的列表
    if in_list and current_key:
        result[current_key] = current_list
    
    return result


def _parse_value(value: str) -> Any:
    """
    解析YAML值
    
    Args:
        value: 值字符串
        
    Returns:
        解析后的值
    """
    value = value.strip()
    
    # 空值
    if not value or value == '~' or value == 'null':
        return None
    
    # 布尔值
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    
    # 数字
    try:
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    
    # 引号字符串
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    
    # 列表形式 [a, b, c]
    if value.startswith('[') and value.endswith(']'):
        inner = value[1:-1]
        items = [item.strip() for item in inner.split(',')]
        return [_parse_value(item) for item in items if item]
    
    return value


def split_path_in_frontmatter(paths_str: str) -> List[str]:
    """
    分割frontmatter中的paths字段
    
    Args:
        paths_str: paths字符串
        
    Returns:
        路径列表
    """
    if not paths_str:
        return []
    
    # 支持逗号分隔或列表格式
    if paths_str.startswith('[') and paths_str.endswith(']'):
        inner = paths_str[1:-1]
        items = [item.strip().strip('"\'') for item in inner.split(',')]
        return [item for item in items if item]
    
    # 逗号分隔
    if ',' in paths_str:
        return [p.strip() for p in paths_str.split(',') if p.strip()]
    
    return [paths_str.strip()]


# 导出
__all__ = [
    "FrontmatterData",
    "parse_frontmatter",
    "split_path_in_frontmatter",
]
