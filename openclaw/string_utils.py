"""
OpenClaw String Utilities
=====================
Inspired by Claude Code's src/utils/stringUtils.ts.

字符串工具，支持：
1. 转义/大小写
2. 复数形式
3. 全角/半角转换
4. 安全拼接
"""

from __future__ import annotations

import re, textwrap
from typing import Optional

# ============================================================================
# 字符串转换
# ============================================================================

def escape_regex(text: str) -> str:
    """转义正则特殊字符"""
    return re.escape(text)

def capitalize(text: str) -> str:
    """
    首字母大写
    
    Example:
        capitalize("hello world") → "Hello world"
        capitalize("fooBar") → "FooBar"
    """
    if not text:
        return text
    return text[0].upper() + text[1:]

def capitalize_words(text: str) -> str:
    """
    每个单词首字母大写
    
    Example:
        capitalize_words("hello world") → "Hello World"
    """
    return " ".join(word.capitalize() for word in text.split())

def snake_case(text: str) -> str:
    """
    转换为 snake_case
    
    Example:
        snake_case("HelloWorld") → "hello_world"
        snake_case("hello-world") → "hello_world"
    """
    # 替换非字母数字为下划线
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower().replace('-', '_').replace(' ', '_')

def camel_case(text: str) -> str:
    """
    转换为 camelCase
    
    Example:
        camel_case("hello_world") → "helloWorld"
    """
    components = text.split('_')
    return components[0] + ''.join(x.capitalize() for x in components[1:])

def kebab_case(text: str) -> str:
    """
    转换为 kebab-case
    
    Example:
        kebab_case("hello_world") → "hello-world"
    """
    return snake_case(text).replace('_', '-')

# ============================================================================
# 复数形式
# ============================================================================

def plural(count: int, word: str, plural_word: Optional[str] = None) -> str:
    """
    复数形式
    
    Example:
        plural(1, "file") → "file"
        plural(3, "file") → "files"
        plural(2, "entry", "entries") → "entries"
    """
    if plural_word is None:
        plural_word = word + "s"
    
    return word if count == 1 else plural_word

def pluralize(count: int, word: str, plural_word: Optional[str] = None) -> str:
    """plural 的别名"""
    return plural(count, word, plural_word)

# ============================================================================
# 全角/半角转换
# ============================================================================

def normalize_fullwidth_digits(text: str) -> str:
    """
    全角数字转半角
    
    Example:
        normalize_fullwidth_digits("１２３") → "123"
    """
    result = []
    for char in text:
        code = ord(char)
        # 全角数字范围：0xFF10 - 0xFF19
        if 0xFF10 <= code <= 0xFF19:
            result.append(chr(code - 0xFF10 + ord('0')))
        else:
            result.append(char)
    return ''.join(result)

def normalize_fullwidth_space(text: str) -> str:
    """
    全角空格转半角
    
    Example:
        normalize_fullwidth_space("Hello　World") → "Hello World"
    """
    return text.replace('\u3000', ' ')  # U+3000 → U+0020

def normalize_fullwidth(text: str) -> str:
    """全角转半角（数字+空格）"""
    text = normalize_fullwidth_digits(text)
    text = normalize_fullwidth_space(text)
    return text

# ============================================================================
# 字符串操作
# ============================================================================

def first_line(text: str) -> str:
    """
    获取第一行
    
    Example:
        first_line("line1\nline2") → "line1"
    """
    nl = text.find('\n')
    if nl == -1:
        return text
    return text[:nl]

def last_line(text: str) -> str:
    """
    获取最后一行
    
    Example:
        last_line("line1\nline2") → "line2"
    """
    nl = text.rfind('\n')
    if nl == -1:
        return text
    return text[nl + 1:]

def count_char(text: str, char: str) -> int:
    """
    统计字符出现次数
    
    Example:
        count_char("hello world", "l") → 3
    """
    return text.count(char)

def count_lines(text: str) -> int:
    """统计行数"""
    if not text:
        return 0
    return text.count('\n') + 1

# ============================================================================
# 安全拼接
# ============================================================================

MAX_STRING_LENGTH = 2 ** 25  # 32MB

def safe_join_lines(lines: list[str], delimiter: str = ",", max_size: int = MAX_STRING_LENGTH) -> str:
    """
    安全拼接字符串（截断如果过长）
    
    Args:
        lines: 字符串列表
        delimiter: 分隔符
        max_size: 最大长度
    
    Returns:
        拼接后的字符串
    """
    if not lines:
        return ""
    
    result = delimiter.join(lines)
    
    if len(result) > max_size:
        # 截断到最大长度
        result = result[:max_size - 3] + "..."
    
    return result

def truncate_middle(text: str, max_length: int) -> str:
    """
    中间截断（保留开头和结尾）
    
    Example:
        truncate_middle("src/components/very/long/Path.tsx", 30) → "src/components/…/Path.tsx"
    """
    if len(text) <= max_length:
        return text
    
    if max_length < 5:
        return text[:max_length]
    
    # 计算可用空间
    ellipsis = "…"
    available = max_length - len(ellipsis)
    start_len = available // 2
    end_len = available - start_len
    
    return text[:start_len] + ellipsis + text[-end_len:]

# ============================================================================
# 缩进和对齐
# ============================================================================

def indent(text: str, spaces: int = 2, skip_first: bool = False) -> str:
    """
    缩进文本
    
    Args:
        text: 文本
        spaces: 缩进空格数
        skip_first: 是否跳过第一行
    """
    prefix = " " * spaces
    lines = text.split('\n')
    
    if skip_first:
        return lines[0] + '\n' + '\n'.join(prefix + line for line in lines[1:])
    else:
        return '\n'.join(prefix + line for line in lines)

def dedent(text: str) -> str:
    """
    去除公共缩进
    
    Example:
        dedent("    hello\n    world") → "hello\nworld"
    """
    lines = text.split('\n')
    
    if not lines:
        return text
    
    # 找出最小缩进
    min_indent = float('inf')
    for line in lines:
        if line.strip():  # 忽略空行
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)
    
    if min_indent == float('inf'):
        min_indent = 0
    
    # 去除公共缩进
    result = []
    for line in lines:
        if line.strip():
            result.append(line[min_indent:])
        else:
            result.append("")
    
    return '\n'.join(result)

def wrap_text(text: str, width: int = 80) -> str:
    """自动换行"""
    return textwrap.fill(text, width=width)

# ============================================================================
# 模板
# ============================================================================

def template(template_str: str, **kwargs) -> str:
    """
    简单模板替换
    
    Example:
        template("Hello ${name}!", name="World") → "Hello World!"
    """
    def replacer(match):
        key = match.group(1)
        return str(kwargs.get(key, match.group(0)))
    
    return re.sub(r'\$\{(\w+)\}', replacer, template_str)

# ============================================================================
# Base64 编码
# ============================================================================

import base64 as b64_module

def base64_encode(text: str) -> str:
    """Base64 编码"""
    return b64_module.b64encode(text.encode()).decode()

def base64_decode(text: str) -> str:
    """Base64 解码"""
    return b64_module.b64decode(text.encode()).decode()

def base64_encode_bytes(data: bytes) -> str:
    """Base64 编码（字节）"""
    return b64_module.b64encode(data).decode()

def base64_decode_bytes(text: str) -> bytes:
    """Base64 解码（字节）"""
    return b64_module.b64decode(text.encode())
