"""
Claude Code Hints - 提示协议
基于 Claude Code claudeCodeHints.ts 设计

解析<claude-code-hint />标签。
"""
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ClaudeCodeHint:
    """Claude Code提示"""
    v: int  # 版本
    type: str  # 类型
    value: str  # 值
    source_command: str  # 源命令


# 支持的版本
SUPPORTED_VERSIONS = {1}

# 支持的类型
SUPPORTED_TYPES = {"plugin"}


def extract_claude_code_hints(
    output: str,
    command: str,
) -> dict:
    """
    从输出中提取Claude Code提示
    
    Args:
        output: 命令输出
        command: 命令
        
    Returns:
        {"hints": list, "stripped": str} - 提示列表和处理后的输出
    """
    # 快速路径：无标签则不处理
    if '<claude-code-hint' not in output:
        return {"hints": [], "stripped": output}
    
    hints: List[ClaudeCodeHint] = []
    lines = output.split('\n')
    kept_lines = []
    
    # 匹配提示标签
    hint_pattern = re.compile(
        r'^[ \t]*<claude-code-hint\s+([^>]*?)\s*/>[ \t]*$'
    )
    # 匹配属性
    attr_pattern = re.compile(r'(\w+)=(?:"([^"]*)"|([^\s/>]+))')
    
    for line in lines:
        match = hint_pattern.match(line)
        if match:
            # 解析属性
            attrs_str = match.group(1)
            attrs = {}
            for attr_match in attr_pattern.finditer(attrs_str):
                key = attr_match.group(1)
                value = attr_match.group(2) or attr_match.group(3)
                attrs[key] = value
            
            # 检查版本和类型
            v = int(attrs.get('v', 0))
            hint_type = attrs.get('type', '')
            
            if v not in SUPPORTED_VERSIONS or hint_type not in SUPPORTED_TYPES:
                # 不支持的版本/类型，跳过但也不保留
                continue
            
            # 提取第一个命令token
            first_token = command.split()[0] if command else ""
            
            hints.append(ClaudeCodeHint(
                v=v,
                type=hint_type,
                value=attrs.get('value', ''),
                source_command=first_token,
            ))
        else:
            kept_lines.append(line)
    
    return {
        "hints": hints,
        "stripped": '\n'.join(kept_lines),
    }


def strip_claude_code_hints(output: str) -> str:
    """
    从输出中移除提示标签
    
    Args:
        output: 命令输出
        
    Returns:
        移除提示后的输出
    """
    # 快速路径
    if '<claude-code-hint' not in output:
        return output
    
    hint_pattern = re.compile(r'^[ \t]*<claude-code-hint\s+[^>]*?\s*/>[ \t]*$', re.MULTILINE)
    return hint_pattern.sub('', output)


# 导出
__all__ = [
    "ClaudeCodeHint",
    "extract_claude_code_hints",
    "strip_claude_code_hints",
    "SUPPORTED_VERSIONS",
    "SUPPORTED_TYPES",
]
