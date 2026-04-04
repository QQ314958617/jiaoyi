"""
Bundled Mode - 运行时检测
基于 Claude Code bundledMode.ts 设计

检测是否运行在Bun或打包模式下。
"""
import os
import sys


def is_running_with_bun() -> bool:
    """
    检测是否运行在Bun环境
    
    Returns:
        是否为Bun环境
    """
    # 检查Bun版本标识
    return hasattr(sys, 'versions') and getattr(sys.versions, 'bun', None) is not None


def is_in_bundled_mode() -> bool:
    """
    检测是否运行在打包的可执行文件中
    
    Returns:
        是否为打包模式
    """
    # Python打包检测（简化）
    # 实际Bun使用embeddedFiles
    return getattr(sys, 'frozen', False)


def is_standalone_executable() -> bool:
    """
    检测是否运行在独立可执行文件中
    
    Returns:
        是否为独立可执行文件
    """
    return (
        getattr(sys, 'frozen', False) or
        '_MEIPASS' in os.environ
    )


# 导出
__all__ = [
    "is_running_with_bun",
    "is_in_bundled_mode",
    "is_standalone_executable",
]
