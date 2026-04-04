"""
Platform - 平台检测工具
基于 Claude Code platform.ts 设计

检测操作系统平台（macOS/Windows/WSL/Linux）。
"""
import os
import platform
import subprocess
from functools import lru_cache
from typing import Literal, Optional

# 平台类型
Platform = Literal['macos', 'windows', 'wsl', 'linux', 'unknown']


@lru_cache(maxsize=1)
def get_platform() -> Platform:
    """
    获取当前平台
    
    Returns:
        平台类型
    """
    system = platform.system().lower()
    
    if system == 'darwin':
        return 'macos'
    
    if system == 'windows':
        return 'windows'
    
    if system == 'linux':
        # 检查是否运行在WSL中
        if _is_wsl():
            return 'wsl'
        return 'linux'
    
    return 'unknown'


def _is_wsl() -> bool:
    """
    检查是否运行在WSL中
    
    Returns:
        是否为WSL
    """
    try:
        with open('/proc/version', 'r') as f:
            content = f.read().lower()
            return 'microsoft' in content or 'wsl' in content
    except Exception:
        return False


@lru_cache(maxsize=1)
def get_wsl_version() -> Optional[str]:
    """
    获取WSL版本
    
    Returns:
        WSL版本号或None
    """
    if get_platform() not in ('wsl', 'linux'):
        return None
    
    try:
        with open('/proc/version', 'r') as f:
            content = f.read()
            
            # 查找WSL版本标记 (WSL2, WSL3等)
            import re
            match = re.search(r'WSL(\d+)', content, re.IGNORECASE)
            if match and match.group(1):
                return match.group(1)
            
            # 如果包含microsoft但没有明确版本，假设WSL1
            if 'microsoft' in content.lower():
                return '1'
            
            return None
            
    except Exception:
        return None


def get_linux_distro_info() -> dict:
    """
    获取Linux发行版信息
    
    Returns:
        发行版信息字典
    """
    if get_platform() != 'linux':
        return {}
    
    result = {
        'linux_distro_id': None,
        'linux_distro_version': None,
        'linux_kernel': platform.release(),
    }
    
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    value = value.strip('"')
                    if key == 'ID':
                        result['linux_distro_id'] = value
                    elif key == 'VERSION_ID':
                        result['linux_distro_version'] = value
                        
    except Exception:
        pass
    
    return result


def detect_vcs(directory: Optional[str] = None) -> list[str]:
    """
    检测版本控制系统
    
    Args:
        directory: 要检测的目录，默认当前目录
        
    Returns:
        检测到的VCS列表
    """
    import os
    
    detected = set()
    target_dir = directory or os.getcwd()
    
    # 检查Perforce环境变量
    if os.environ.get('P4PORT'):
        detected.add('perforce')
    
    # VCS标记
    vcs_markers = [
        ('.git', 'git'),
        ('.hg', 'mercurial'),
        ('.svn', 'svn'),
        ('.p4config', 'perforce'),
        ('$tf', 'tfs'),
        ('.tfvc', 'tfs'),
        ('.jj', 'jujutsu'),
        ('.sl', 'sapling'),
    ]
    
    try:
        entries = set(os.listdir(target_dir))
        for marker, vcs in vcs_markers:
            if marker in entries:
                detected.add(vcs)
    except Exception:
        pass
    
    return list(detected)


def is_macos() -> bool:
    """是否为macOS"""
    return get_platform() == 'macos'


def is_windows() -> bool:
    """是否为Windows"""
    return get_platform() == 'windows'


def is_wsl() -> bool:
    """是否为WSL"""
    return get_platform() == 'wsl'


def is_linux() -> bool:
    """是否为Linux"""
    return get_platform() == 'linux'


# 导出
__all__ = [
    "Platform",
    "get_platform",
    "get_wsl_version",
    "get_linux_distro_info",
    "detect_vcs",
    "is_macos",
    "is_windows",
    "is_wsl",
    "is_linux",
]
