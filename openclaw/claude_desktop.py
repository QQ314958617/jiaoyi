"""
Claude Desktop - Claude桌面配置
基于 Claude Code claudeDesktop.ts 设计

读取Claude桌面配置。
"""
import os
import json
from pathlib import Path
from typing import Optional


def get_claude_desktop_config_path() -> str:
    """
    获取Claude桌面配置文件路径
    
    Returns:
        配置文件路径
    """
    platform = _get_platform()
    
    if platform == 'macos':
        return str(Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json')
    
    elif platform == 'wsl':
        # Windows下的路径
        userprofile = os.environ.get('USERPROFILE', '')
        if userprofile:
            # 移除驱动器字母
            path = userprofile.replace('\\', '/').replace(':', '')
            config_path = f"/mnt/{path[0].lower()}{path[2:]}/AppData/Roaming/Claude/claude_desktop_config.json"
            if os.path.exists(config_path):
                return config_path
        
        # 尝试查找用户目录
        try:
            users_dir = '/mnt/c/Users'
            if os.path.isdir(users_dir):
                for user in os.listdir(users_dir):
                    if user in ('Public', 'Default', 'Default User', 'All Users'):
                        continue
                    config_path = f"/mnt/c/Users/{user}/AppData/Roaming/Claude/claude_desktop_config.json"
                    if os.path.exists(config_path):
                        return config_path
        except Exception:
            pass
    
    raise ValueError(f"Unsupported platform: {platform}")


def _get_platform() -> str:
    """获取平台"""
    import platform as p
    system = p.system().lower()
    if system == 'darwin':
        return 'macos'
    elif system == 'windows':
        return 'windows'
    elif system == 'linux':
        # 检查WSL
        try:
            with open('/proc/version', 'r') as f:
                content = f.read().lower()
                if 'microsoft' in content or 'wsl' in content:
                    return 'wsl'
        except Exception:
            pass
        return 'linux'
    return 'unknown'


def read_claude_desktop_mcp_servers() -> dict:
    """
    读取Claude桌面的MCP服务器配置
    
    Returns:
        MCP服务器配置字典
    """
    try:
        config_path = get_claude_desktop_config_path()
    except ValueError:
        return {}
    
    if not os.path.exists(config_path):
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception:
        return {}
    
    if not config or not isinstance(config, dict):
        return {}
    
    mcp_servers = config.get('mcpServers')
    if not mcp_servers or not isinstance(mcp_servers, dict):
        return {}
    
    result = {}
    for name, server_config in mcp_servers.items():
        if not server_config or not isinstance(server_config, dict):
            continue
        
        # 简单验证
        if 'command' in server_config:
            result[name] = server_config
    
    return result


# 导出
__all__ = [
    "get_claude_desktop_config_path",
    "read_claude_desktop_mcp_servers",
]
