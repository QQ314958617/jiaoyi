"""
Color - 颜色工具
基于 Claude Code color.ts 设计

颜色处理工具。
"""
import re
from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    HEX转RGB
    
    Args:
        hex_color: 十六进制颜色 (#RRGGBB)
        
    Returns:
        (R, G, B) 元组
    """
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    RGB转HEX
    
    Args:
        r: 红色 (0-255)
        g: 绿色 (0-255)
        b: 蓝色 (0-255)
        
    Returns:
        十六进制颜色字符串
    """
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def rgb_to_hsl(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    RGB转HSL
    
    Args:
        r: 红色 (0-255)
        g: 绿色 (0-255)
        b: 蓝色 (0-255)
        
    Returns:
        (H, S, L) 元组，H是0-360，S和L是0-100
    """
    r, g, b = r / 255, g / 255, b / 255
    
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2
    
    if max_c == min_c:
        h = s = 0
    else:
        d = max_c - min_c
        s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
        
        if max_c == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_c == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        
        h /= 6
    
    return (h * 360, s * 100, l * 100)


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """
    HSL转RGB
    
    Args:
        h: 色相 (0-360)
        s: 饱和度 (0-100)
        l: 亮度 (0-100)
        
    Returns:
        (R, G, B) 元组
    """
    h = h / 360
    s = s / 100
    l = l / 100
    
    if s == 0:
        v = int(l * 255)
        return (v, v, v)
    
    def hue_to_rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p
    
    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    
    return (
        int(hue_to_rgb(p, q, h + 1/3) * 255),
        int(hue_to_rgb(p, q, h) * 255),
        int(hue_to_rgb(p, q, h - 1/3) * 255),
    )


def lighten(hex_color: str, amount: float) -> str:
    """
    变亮
    
    Args:
        hex_color: 颜色
        amount: 变亮程度 (0-100)
        
    Returns:
        变亮后的颜色
    """
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    l = min(100, l + amount)
    rgb = hsl_to_rgb(h, s, l)
    return rgb_to_hex(*rgb)


def darken(hex_color: str, amount: float) -> str:
    """
    变暗
    
    Args:
        hex_color: 颜色
        amount: 变暗程度 (0-100)
        
    Returns:
        变暗后的颜色
    """
    return lighten(hex_color, -amount)


def saturate(hex_color: str, amount: float) -> str:
    """
    增加饱和度
    
    Args:
        hex_color: 颜色
        amount: 增加程度 (0-100)
        
    Returns:
        增强后的颜色
    """
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    s = min(100, s + amount)
    rgb = hsl_to_rgb(h, s, l)
    return rgb_to_hex(*rgb)


def desaturate(hex_color: str, amount: float) -> str:
    """
    降低饱和度
    
    Args:
        hex_color: 颜色
        amount: 降低程度 (0-100)
        
    Returns:
        降低后的颜色
    """
    return saturate(hex_color, -amount)


def is_valid_hex(hex_color: str) -> bool:
    """
    检查是否为有效HEX颜色
    
    Args:
        hex_color: 颜色字符串
        
    Returns:
        是否有效
    """
    return bool(re.match(r'^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$', hex_color))


# 导出
__all__ = [
    "hex_to_rgb",
    "rgb_to_hex",
    "rgb_to_hsl",
    "hsl_to_rgb",
    "lighten",
    "darken",
    "saturate",
    "desaturate",
    "is_valid_hex",
]
