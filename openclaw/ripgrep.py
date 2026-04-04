"""
Ripgrep - grep工具封装
基于 Claude Code ripgrep.ts 设计

封装ripgrep命令调用。
"""
import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class RipgrepResult:
    """Ripgrep结果"""
    matches: List[dict]
    total_matches: int


def get_ripgrep_command() -> Tuple[str, List[str], Optional[str]]:
    """
    获取ripgrep命令配置
    
    Returns:
        (rg_path, args, argv0)
    """
    # 优先使用系统rg
    import shutil
    
    rg_path = shutil.which('rg')
    if rg_path:
        return ('rg', [], None)
    
    # 使用bundled rg（简化处理）
    return ('rg', [], None)


def ripgrep(
    pattern: str,
    paths: List[str],
    options: Optional[dict] = None,
) -> RipgrepResult:
    """
    执行ripgrep搜索
    
    Args:
        pattern: 搜索模式
        paths: 要搜索的文件路径
        options: 选项
        
    Returns:
        RipgrepResult
    """
    options = options or {}
    
    rg_path, base_args, argv0 = get_ripgrep_command()
    
    args = [
        '--json',
        '--line-number',
    ]
    
    # 添加选项
    if options.get('case_sensitive') is False:
        args.append('--ignore-case')
    
    if options.get('hidden'):
        args.append('--hidden')
    
    if options.get('follow'):
        args.append('--follow')
    
    if 'max_count' in options:
        args.extend(['--max-count', str(options['max_count'])])
    
    if 'glob' in options:
        args.extend(['--glob', options['glob']])
    
    if 'include' in options:
        args.extend(['--include', options['include']])
    
    if 'exclude' in options:
        args.extend(['--exclude', options['exclude']])
    
    # 添加搜索模式
    args.append(pattern)
    
    # 添加路径
    args.extend(paths)
    
    try:
        result = subprocess.run(
            [rg_path] + args,
            capture_output=True,
            text=True,
            timeout=options.get('timeout', 30),
        )
        
        matches = []
        for line in result.stdout.split('\n'):
            if line.strip():
                try:
                    import json
                    match = json.loads(line)
                    matches.append(match)
                except Exception:
                    pass
        
        return RipgrepResult(
            matches=matches,
            total_matches=len(matches),
        )
        
    except Exception as e:
        return RipgrepResult(matches=[], total_matches=0)


def count_files_rounded_rg(
    pattern: str,
    path: str,
    options: Optional[dict] = None,
) -> int:
    """
    统计匹配的文件数
    
    Args:
        pattern: 搜索模式
        path: 搜索路径
        options: 选项
        
    Returns:
        匹配文件数
    """
    options = options or {}
    options['max_count'] = 1
    
    result = ripgrep(pattern, [path], options)
    
    # 统计唯一文件
    files = set()
    for match in result.matches:
        if 'data' in match and 'lines' in match['data']:
            if 'path' in match['data']:
                files.add(match['data']['path']['text'])
    
    return len(files)


# 导出
__all__ = [
    "RipgrepResult",
    "get_ripgrep_command",
    "ripgrep",
    "count_files_rounded_rg",
]
