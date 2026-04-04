"""
Argument Substitution - 参数替换工具
基于 Claude Code argumentSubstitution.ts 设计

替换skill/command提示中的$ARGUMENTS占位符。
"""
import re
from typing import List, Optional


def parse_arguments(args: str) -> List[str]:
    """
    解析参数字符串为数组
    
    使用简单的空格分割，支持引号包围。
    
    Args:
        args: 参数字符串
        
    Returns:
        参数列表
        
    Example:
        >>> parse_arguments('foo "hello world" baz')
        ['foo', 'hello world', 'baz']
    """
    if not args or not args.strip():
        return []
    
    # 简单的引号解析
    result = []
    current = []
    in_quote = False
    quote_char = None
    
    i = 0
    while i < len(args):
        c = args[i]
        
        if c in ('"', "'") and not in_quote:
            in_quote = True
            quote_char = c
        elif c == quote_char and in_quote:
            in_quote = False
            quote_char = None
        elif c in (' ', '\t', '\n') and not in_quote:
            if current:
                result.append(''.join(current))
                current = []
        else:
            current.append(c)
        
        i += 1
    
    if current:
        result.append(''.join(current))
    
    return result


def parse_argument_names(argument_names: Optional[str | List[str]]) -> List[str]:
    """
    解析参数名称
    
    Args:
        argument_names: 参数名称（字符串或列表）
        
    Returns:
        参数名称列表
    """
    if not argument_names:
        return []
    
    if isinstance(argument_names, list):
        # 过滤空字符串和纯数字名称
        return [
            n for n in argument_names
            if isinstance(n, str) and n.strip() and not n.strip().isdigit()
        ]
    
    if isinstance(argument_names, str):
        return argument_names.split()
    
    return []


def generate_progressive_argument_hint(
    arg_names: List[str],
    typed_args: List[str],
) -> Optional[str]:
    """
    生成渐进式参数提示
    
    Args:
        arg_names: 参数名称列表
        typed_args: 已输入的参数列表
        
    Returns:
        提示字符串或None
    """
    remaining = arg_names[len(typed_args):]
    if not remaining:
        return None
    return ' '.join(f"[{name}]" for name in remaining)


def substitute_arguments(
    content: str,
    args: Optional[str],
    append_if_no_placeholder: bool = True,
    argument_names: Optional[List[str]] = None,
) -> str:
    """
    替换$ARGUMENTS占位符
    
    支持：
    - $ARGUMENTS - 替换为完整参数字符串
    - $ARGUMENTS[0], $ARGUMENTS[1] - 替换为索引参数
    - $0, $1 - 索引参数的简写
    - $foo, $bar - 命名参数
    
    Args:
        content: 包含占位符的内容
        args: 参数字符串
        append_if_no_placeholder: 无占位符时是否追加
        argument_names: 命名参数列表
        
    Returns:
        替换后的内容
    """
    if args is None:
        return content
    
    argument_names = argument_names or []
    parsed_args = parse_arguments(args) if args else []
    original_content = content
    
    # 替换命名参数
    for i, name in enumerate(argument_names):
        if not name:
            continue
        # 匹配 $name 但不是 $name[ 或 $nameXxx
        pattern = rf'\${re.escape(name)}(?!\w|\[)'
        replacement = parsed_args[i] if i < len(parsed_args) else ''
        content = re.sub(pattern, replacement, content)
    
    # 替换索引参数 $ARGUMENTS[0]
    def replace_indexed(match):
        index = int(match.group(1))
        return parsed_args[index] if index < len(parsed_args) else ''
    
    content = re.sub(r'\$ARGUMENTS\[(\d+)\]', replace_indexed, content)
    
    # 替换简写 $0, $1
    def replace_shorthand(match):
        index = int(match.group(1))
        return parsed_args[index] if index < len(parsed_args) else ''
    
    content = re.sub(r'\$(\d+)(?!\w)', replace_shorthand, content)
    
    # 替换$ARGUMENTS
    content = content.replace('$ARGUMENTS', args)
    
    # 如果没有替换且启用追加
    if content == original_content and append_if_no_placeholder and args:
        content = f"{content}\n\nARGUMENTS: {args}"
    
    return content


# 导出
__all__ = [
    "parse_arguments",
    "parse_argument_names",
    "generate_progressive_argument_hint",
    "substitute_arguments",
]
