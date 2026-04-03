"""
OpenClaw Context Analyzer
========================
Inspired by Claude Code's src/utils/contextAnalysis.ts (272 lines).

核心功能：
1. 消息 token 统计（用户/助手/工具）
2. 工具使用统计（调用次数 + token 消耗）
3. 重复文件读取检测（节省 token）
4. 上下文优化建议

Claude Code 的设计：
- analyzeContext(): 返回 TokenStats（按类型/工具/文件统计）
- duplicateFileReads: 同一文件被读取多次的 token 浪费
- processBlock(): 按消息块类型累计 token

我们的用途：
- 交易系统的 AI 对话上下文优化
- 减少重复读取文件/数据
- 提供上下文压缩建议
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime, timezone, timedelta


# ============================================================================
# Token 估算（简化版）
# ============================================================================

def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量。

    简单估算：中文 ≈ 字数 * 1.5，英文 ≈ 单词数 * 1.3
    Claude 约 4 字符 = 1 token
    """
    if not text:
        return 0

    # 中文
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))

    # 英文和数字（粗略）
    english_words = len(re.findall(r'[a-zA-Z0-9]+', text))

    # 标点和空白
    other = len(re.findall(r'[^\sa-zA-Z0-9\u4e00-\u9fff]', text))

    # 估算：中文 1.5，中文 1，英文单词 1.3，其他 0.5
    return int(chinese_chars * 1.5 + english_words * 1.3 + other * 0.5)


def estimate_tokens_for_object(obj: Any) -> int:
    """估算任意对象的 token 数量（JSON 序列化后估算）"""
    try:
        text = json.dumps(obj, ensure_ascii=False, default=str)
        return estimate_tokens(text)
    except Exception:
        return 0


# ============================================================================
# Token 统计
# ============================================================================

@dataclass
class TokenStats:
    """Token 统计结果"""
    # 按消息类型
    human_message_tokens: int = 0
    assistant_message_tokens: int = 0
    system_message_tokens: int = 0

    # 按工具类型
    tool_use_tokens: Dict[str, int] = field(default_factory=dict)  # tool_name -> tokens
    tool_result_tokens: Dict[str, int] = field(default_factory=dict)

    # 本地命令输出
    local_command_output_tokens: int = 0

    # 其他
    other_tokens: int = 0

    # 重复读取
    duplicate_file_reads: Dict[str, int] = field(default_factory=dict)  # path -> wasted_tokens

    # 附件
    attachment_tokens: Dict[str, int] = field(default_factory=dict)  # type -> count

    # 总计
    total_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "human_message_tokens": self.human_message_tokens,
            "assistant_message_tokens": self.assistant_message_tokens,
            "system_message_tokens": self.system_message_tokens,
            "tool_use_tokens": dict(self.tool_use_tokens),
            "tool_result_tokens": dict(self.tool_result_tokens),
            "local_command_output_tokens": self.local_command_output_tokens,
            "other_tokens": self.other_tokens,
            "duplicate_file_reads": dict(self.duplicate_file_reads),
            "attachment_tokens": dict(self.attachment_tokens),
            "total_tokens": self.total_tokens,
        }

    def summary(self) -> str:
        """生成可读摘要"""
        lines = [
            f"📊 Token 统计",
            f"  人类消息: {self.human_message_tokens:,} tokens",
            f"  AI回复:   {self.assistant_message_tokens:,} tokens",
            f"  系统消息: {self.system_message_tokens:,} tokens",
            f"  工具调用: {sum(self.tool_use_tokens.values()):,} tokens",
            f"  工具结果: {sum(self.tool_result_tokens.values()):,} tokens",
            f"  本地命令: {self.local_command_output_tokens:,} tokens",
            f"  总计:     {self.total_tokens:,} tokens",
        ]

        if self.tool_use_tokens:
            lines.append("  ---")
            lines.append("  工具使用:")
            for tool, tokens in sorted(self.tool_use_tokens.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"    {tool}: {tokens:,} tokens")

        if self.duplicate_file_reads:
            lines.append("  ---")
            lines.append("  ⚠️ 重复文件读取（可优化）:")
            for path, wasted in sorted(self.duplicate_file_reads.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"    {path}: {wasted:,} tokens 浪费")

        return "\n".join(lines)


# ============================================================================
# 消息块处理
# ============================================================================

def _process_text_block(text: str, is_human: bool) -> Tuple[str, int]:
    """处理文本块"""
    tokens = estimate_tokens(text)

    # 检查是否是本地命令输出
    if "local-command-stdout" in text or "[local command output]" in text:
        return ("local_command", tokens)
    elif is_human:
        return ("human", tokens)
    else:
        return ("assistant", tokens)


def _process_tool_use(tool_name: str, tool_id: str, tool_input: Any, tokens: int,
                      tool_ids: Dict[str, str],
                      read_tool_paths: Dict[str, str]) -> None:
    """处理工具调用块"""
    tool_ids[tool_id] = tool_name

    # 追踪 Read 工具的文件路径
    if tool_name == "Read" and tool_input:
        path = _extract_file_path(tool_input)
        if path:
            read_tool_paths[tool_id] = path


def _process_tool_result(tool_result: Any, tool_id: str, tokens: int,
                        tool_ids: Dict[str, str],
                        read_tool_paths: Dict[str, str],
                        file_read_stats: Dict[str, Dict]) -> None:
    """处理工具结果块"""
    tool_name = tool_ids.get(tool_id, "unknown")

    # 追踪文件读取
    if tool_name == "Read" and tool_id in read_tool_paths:
        path = read_tool_paths[tool_id]
        if path not in file_read_stats:
            file_read_stats[path] = {"count": 0, "total_tokens": 0}
        file_read_stats[path]["count"] += 1
        file_read_stats[path]["total_tokens"] += tokens


def _extract_file_path(tool_input: Any) -> Optional[str]:
    """从工具输入中提取文件路径"""
    if isinstance(tool_input, dict):
        for key in ["file_path", "path", "file", "filepath"]:
            if key in tool_input:
                return str(tool_input[key])
    elif isinstance(tool_input, str):
        return tool_input
    return None


# ============================================================================
# 核心分析函数
# ============================================================================

def analyze_context(messages: List[Dict[str, Any]]) -> TokenStats:
    """
    分析消息列表的 token 使用情况。

    对应 Claude Code 的 analyzeContext()。

    Args:
        messages: 消息列表，每条消息格式：
            {
                "role": "user" | "assistant" | "system",
                "content": str | List[Dict],  # 文本或块列表
                "type": "message" | "tool_call" | "tool_result",  # 可选
            }

    Returns:
        TokenStats 对象
    """
    stats = TokenStats()
    tool_ids: Dict[str, str] = {}  # id -> tool_name
    read_tool_paths: Dict[str, str] = {}  # tool_id -> file_path
    file_read_stats: Dict[str, Dict] = {}  # path -> {count, total_tokens}

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "system":
            tokens = estimate_tokens_for_object(content)
            stats.system_message_tokens += tokens
            stats.total_tokens += tokens
            continue

        if isinstance(content, str):
            # 纯文本消息
            category, tokens = _process_text_block(content, role == "user")
            if category == "local_command":
                stats.local_command_output_tokens += tokens
            elif category == "human":
                stats.human_message_tokens += tokens
            else:
                stats.assistant_message_tokens += tokens
            stats.total_tokens += tokens

        elif isinstance(content, list):
            # 块列表
            for block in content:
                if not isinstance(block, dict):
                    continue

                block_type = block.get("type", "")
                tokens = estimate_tokens_for_object(block)

                if block_type == "text":
                    text = block.get("text", "")
                    category, _ = _process_text_block(text, role == "user")
                    if category == "local_command":
                        stats.local_command_output_tokens += tokens
                    elif category == "human":
                        stats.human_message_tokens += tokens
                    else:
                        stats.assistant_message_tokens += tokens
                    stats.total_tokens += tokens

                elif block_type == "tool_use":
                    tool_name = block.get("name", "unknown")
                    tool_id = block.get("id", str(len(tool_ids)))
                    tool_input = block.get("input", {})

                    if tool_name not in stats.tool_use_tokens:
                        stats.tool_use_tokens[tool_name] = 0
                    stats.tool_use_tokens[tool_name] += tokens
                    stats.total_tokens += tokens

                    _process_tool_use(
                        tool_name, tool_id, tool_input, tokens,
                        tool_ids, read_tool_paths
                    )

                elif block_type == "tool_result":
                    tool_id = block.get("tool_use_id", "")
                    tool_content = block.get("content", "")

                    tool_name = tool_ids.get(tool_id, "unknown")
                    if tool_name not in stats.tool_result_tokens:
                        stats.tool_result_tokens[tool_name] = 0
                    stats.tool_result_tokens[tool_name] += tokens
                    stats.total_tokens += tokens

                    _process_tool_result(
                        tool_content, tool_id, tokens,
                        tool_ids, read_tool_paths, file_read_stats
                    )

                elif block_type == "image":
                    if "image_url" not in stats.attachment_tokens:
                        stats.attachment_tokens["image"] = 0
                    stats.attachment_tokens["image"] += 1

                else:
                    # 其他类型
                    stats.other_tokens += tokens
                    stats.total_tokens += tokens

        else:
            # 其他格式
            tokens = estimate_tokens_for_object(content)
            stats.other_tokens += tokens
            stats.total_tokens += tokens

    # 计算重复文件读取的 token 浪费
    for path, data in file_read_stats.items():
        if data["count"] > 1:
            avg_tokens = data["total_tokens"] // data["count"]
            wasted = avg_tokens * (data["count"] - 1)
            stats.duplicate_file_reads[path] = wasted

    return stats


# ============================================================================
# 上下文优化建议
# ============================================================================

@dataclass
class OptimizationSuggestion:
    """优化建议"""
    category: str  # "duplicate_read" | "long_output" | "context_too_long"
    severity: str  # "high" | "medium" | "low"
    description: str
    estimated_savings: int  # tokens
    action: str


def get_optimization_suggestions(stats: TokenStats) -> List[OptimizationSuggestion]:
    """
    根据统计生成优化建议。

    对应 Claude Code 的上下文优化建议。
    """
    suggestions = []

    # 重复文件读取
    for path, wasted in stats.duplicate_file_reads.items():
        if wasted > 1000:
            suggestions.append(OptimizationSuggestion(
                category="duplicate_read",
                severity="high" if wasted > 5000 else "medium",
                description=f"文件 {path} 被读取 {len(stats.duplicate_file_reads)} 次",
                estimated_savings=wasted,
                action=f"使用缓存，避免重复读取同一文件"
            ))

    # 本地命令输出过大
    if stats.local_command_output_tokens > 5000:
        suggestions.append(OptimizationSuggestion(
            category="long_output",
            severity="medium",
            description=f"本地命令输出了 {stats.local_command_output_tokens:,} tokens",
            estimated_savings=int(stats.local_command_output_tokens * 0.5),
            action="考虑只保留关键输出行，或使用 head/tail 限制"
        ))

    # 上下文过长
    if stats.total_tokens > 150000:
        suggestions.append(OptimizationSuggestion(
            category="context_too_long",
            severity="high",
            description=f"上下文总计 {stats.total_tokens:,} tokens，超过推荐限制",
            estimated_savings=int(stats.total_tokens * 0.3),
            action="启用上下文压缩或摘要，移除旧消息"
        ))

    return sorted(suggestions, key=lambda s: -s.estimated_savings)


# ============================================================================
# 便捷函数
# ============================================================================

def analyze_and_summarize(messages: List[Dict[str, Any]]) -> str:
    """分析并生成摘要"""
    stats = analyze_context(messages)
    suggestions = get_optimization_suggestions(stats)

    lines = [stats.summary()]

    if suggestions:
        lines.append("")
        lines.append("💡 优化建议:")
        for s in suggestions[:3]:
            lines.append(f"  [{s.severity.upper()}] {s.description}")
            lines.append(f"         预计节省: {s.estimated_savings:,} tokens")

    return "\n".join(lines)


def quick_token_count(text: str) -> int:
    """快速 token 计数"""
    return estimate_tokens(text)
