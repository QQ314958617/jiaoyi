"""
OpenClaw File Utilities
====================
Inspired by Claude Code's src/utils/file.ts.

文件操作工具，支持：
1. 安全读写
2. 编码检测
3. 文件监控
4. 行尾处理
"""

from __future__ import annotations

import os, mimetypes, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# ============================================================================
# 文件存在检查
# ============================================================================

def path_exists(path: str) -> bool:
    """检查路径是否存在"""
    return os.path.exists(path)

def is_file(path: str) -> bool:
    """检查是否是文件"""
    return os.path.isfile(path)

def is_dir(path: str) -> bool:
    """检查是否是目录"""
    return os.path.isdir(path)

# ============================================================================
# 文件读取
# ============================================================================

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def read_file_safe(path: str, encoding: str = "utf-8") -> Optional[str]:
    """
    安全读取文件
    
    失败返回 None
    """
    try:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            return f.read()
    except (IOError, OSError):
        return None

def read_file_lines(path: str, encoding: str = "utf-8") -> list[str]:
    """读取文件所有行"""
    try:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            return f.readlines()
    except (IOError, OSError):
        return []

def read_file_chunks(path: str, chunk_size: int = 8192) -> list[bytes]:
    """分块读取文件"""
    chunks = []
    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
    except (IOError, OSError):
        pass
    return chunks

# ============================================================================
# 文件写入
# ============================================================================

def write_file_safe(path: str, content: str, encoding: str = "utf-8") -> bool:
    """
    安全写入文件
    
    成功返回 True
    """
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except (IOError, OSError):
        return False

def write_file_atomic(path: str, content: str, encoding: str = "utf-8") -> bool:
    """
    原子写入文件（先写临时文件再重命名）
    
    更安全，但需要额外磁盘空间
    """
    import tempfile, shutil
    
    try:
        dir_name = os.path.dirname(path) or "."
        os.makedirs(dir_name, exist_ok=True)
        
        # 创建临时文件
        fd, tmp_path = tempfile.mkstemp(dir=dir_name)
        os.close(fd)
        
        try:
            with open(tmp_path, "w", encoding=encoding) as f:
                f.write(content)
            
            # 重命名为目标文件
            shutil.move(tmp_path, path)
            return True
        except:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass
            raise
    except Exception:
        return False

def append_file(path: str, content: str, encoding: str = "utf-8") -> bool:
    """追加写入文件"""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding=encoding) as f:
            f.write(content)
        return True
    except (IOError, OSError):
        return False

# ============================================================================
# 文件信息
# ============================================================================

def get_file_size(path: str) -> int:
    """获取文件大小（字节）"""
    try:
        return os.path.getsize(path)
    except (IOError, OSError):
        return 0

def get_file_mtime(path: str) -> Optional[datetime]:
    """获取文件修改时间"""
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts, timezone(timedelta(hours=8)))
    except (IOError, OSError):
        return None

def get_file_ctime(path: str) -> Optional[datetime]:
    """获取文件创建时间（Linux 上是 inode 修改时间）"""
    try:
        ts = os.path.getctime(path)
        return datetime.fromtimestamp(ts, timezone(timedelta(hours=8)))
    except (IOError, OSError):
        return None

def format_file_size(size: int) -> str:
    """格式化文件大小"""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f}MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f}GB"

# ============================================================================
# 编码检测
# ============================================================================

def detect_encoding(path: str) -> str:
    """
    检测文件编码
    
    简单实现：检查 BOM 或尝试解码
    """
    try:
        with open(path, "rb") as f:
            raw = f.read(4096)
        
        # 检查 BOM
        if raw.startswith(b'\xef\xbb\xbf'):
            return "utf-8-sig"
        elif raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
            return "utf-16"
        
        # 尝试解码
        for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
            try:
                raw.decode(enc)
                return enc
            except UnicodeDecodeError:
                continue
        
        return "utf-8"
    except (IOError, OSError):
        return "utf-8"

# ============================================================================
# 行尾处理
# ============================================================================

def normalize_line_endings(content: str, target: str = "LF") -> str:
    """
    标准化行尾
    
    Args:
        content: 文件内容
        target: 目标行尾 ("LF", "CRLF", "CR")
    """
    # 先统一转换为 LF
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # 转换为目标格式
    if target == "CRLF":
        content = content.replace('\n', '\r\n')
    elif target == "CR":
        content = content.replace('\n', '\r')
    
    return content

def detect_line_endings(content: str) -> str:
    """
    检测行尾类型
    
    Returns: "CRLF", "LF", 或 "CR"
    """
    if '\r\n' in content:
        return "CRLF"
    elif '\r' in content:
        return "CR"
    else:
        return "LF"

# ============================================================================
# 文件哈希
# ============================================================================

def file_hash(path: str, algorithm: str = "sha256") -> Optional[str]:
    """
    计算文件哈希
    
    Args:
        path: 文件路径
        algorithm: 哈希算法（md5, sha1, sha256）
    """
    try:
        h = hashlib.new(algorithm)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except (IOError, OSError):
        return None

def content_hash(content: str, algorithm: str = "sha256") -> str:
    """计算内容哈希"""
    h = hashlib.new(algorithm)
    h.update(content.encode("utf-8"))
    return h.hexdigest()

# ============================================================================
# MIME 类型
# ============================================================================

def get_mime_type(path: str) -> str:
    """获取文件的 MIME 类型"""
    mime, _ = mimetypes.guess_type(path)
    return mime or "application/octet-stream"

def is_text_file(path: str) -> bool:
    """判断是否是文本文件"""
    # 检查 MIME 类型
    mime = get_mime_type(path)
    if mime.startswith("text/"):
        return True
    
    # 检查扩展名
    text_extensions = {".txt", ".md", ".py", ".js", ".ts", ".json", ".xml", ".yaml", ".yml", ".csv"}
    ext = os.path.splitext(path)[1].lower()
    if ext in text_extensions:
        return True
    
    # 尝试读取判断
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
        
        # 检查是否包含空字节（可能是二进制）
        if b'\x00' in chunk:
            return False
        
        # 尝试解码
        chunk.decode("utf-8")
        return True
    except:
        return False

# ============================================================================
# 文件比较
# ============================================================================

def files_identical(path1: str, path2: str) -> bool:
    """比较两个文件是否相同"""
    # 大小比较
    if get_file_size(path1) != get_file_size(path2):
        return False
    
    # 哈希比较
    h1 = file_hash(path1)
    h2 = file_hash(path2)
    if h1 is None or h2 is None:
        return False
    
    return h1 == h2

def diff_files(path1: str, path2: str) -> list[str]:
    """简单文件对比（返回差异行）"""
    lines1 = read_file_lines(path1)
    lines2 = read_file_lines(path2)
    
    diff = []
    max_len = max(len(lines1), len(lines2))
    
    for i in range(max_len):
        l1 = lines1[i] if i < len(lines1) else None
        l2 = lines2[i] if i < len(lines2) else None
        
        if l1 != l2:
            if l1 is not None:
                diff.append(f"- {l1.rstrip()}")
            if l2 is not None:
                diff.append(f"+ {l2.rstrip()}")
    
    return diff
