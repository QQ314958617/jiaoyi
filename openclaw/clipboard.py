"""
Clipboard - 剪贴板
基于 Claude Code clipboard.ts 设计

剪贴板工具。
"""
import subprocess


def copy(text: str) -> bool:
    """
    复制到剪贴板
    
    Args:
        text: 文本
        
    Returns:
        是否成功
    """
    try:
        # Linux: xclip 或 xsel
        process = subprocess.Popen(
            ['xclip', '-selection', 'clipboard'],
            stdin=subprocess.PIPE
        )
        process.communicate(input=text.encode())
        return True
    except FileNotFoundError:
        try:
            # 备用 xsel
            process = subprocess.Popen(
                ['xsel', '--clipboard', '--input'],
                stdin=subprocess.PIPE
            )
            process.communicate(input=text.encode())
            return True
        except FileNotFoundError:
            return False


def paste() -> str:
    """
    从剪贴板粘贴
    
    Returns:
        剪贴板内容
    """
    try:
        process = subprocess.Popen(
            ['xclip', '-selection', 'clipboard', '-o'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, _ = process.communicate()
        return stdout.decode()
    except FileNotFoundError:
        try:
            process = subprocess.Popen(
                ['xsel', '--clipboard', '--output'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = process.communicate()
            return stdout.decode()
        except FileNotFoundError:
            return ""


def copy_image(image_path: str) -> bool:
    """
    复制图片到剪贴板
    
    Args:
        image_path: 图片路径
    """
    try:
        process = subprocess.Popen(
            ['xclip', '-selection', 'clipboard', '-t', 'image/png', '-i', image_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        process.communicate()
        return True
    except FileNotFoundError:
        return False


# 导出
__all__ = [
    "copy",
    "paste",
    "copy_image",
]
