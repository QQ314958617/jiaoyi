"""
Attachments System - 附件系统
基于 Claude Code attachments.ts 设计

附件是在AI对话中注入的上下文信息，包括：
- 文件内容(@提及的文件)
- 变更文件
- 记忆文件
- 待办提醒
- Agent提及
- MCP资源
- 等等
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import json
import re

from .errors import error_message, log_error


# 配置常量
MAX_MEMORY_LINES = 200
MAX_MEMORY_BYTES = 4096
MAX_SESSION_BYTES = 60 * 1024


class AttachmentType(Enum):
    """附件类型枚举"""
    FILE = "file"
    COMPACT_FILE_REFERENCE = "compact_file_reference"
    PDF_REFERENCE = "pdf_reference"
    ALREADY_READ_FILE = "already_read_file"
    EDITED_TEXT_FILE = "edited_text_file"
    EDITED_IMAGE_FILE = "edited_image_file"
    DIRECTORY = "directory"
    SELECTED_LINES_IN_IDE = "selected_lines_in_ide"
    OPENED_FILE_IN_IDE = "opened_file_in_ide"
    TODO_REMINDER = "todo_reminder"
    TASK_REMINDER = "task_reminder"
    NESTED_MEMORY = "nested_memory"
    RELEVANT_MEMORIES = "relevant_memories"
    DYNAMIC_SKILL = "dynamic_skill"
    SKILL_LISTING = "skill_listing"
    SKILL_DISCOVERY = "skill_discovery"
    QUEUED_COMMAND = "queued_command"
    OUTPUT_STYLE = "output_style"
    DIAGNOSTICS = "diagnostics"
    PLAN_MODE = "plan_mode"
    PLAN_MODE_EXIT = "plan_mode_exit"
    AUTO_MODE = "auto_mode"
    AUTO_MODE_EXIT = "auto_mode_exit"
    CRITICAL_SYSTEM_REMINDER = "critical_system_reminder"
    MCP_RESOURCE = "mcp_resource"
    COMMAND_PERMISSIONS = "command_permissions"
    AGENT_MENTION = "agent_mention"
    TASK_STATUS = "task_status"
    TOKEN_USAGE = "token_usage"
    BUDGET_USD = "budget_usd"
    OUTPUT_TOKEN_USAGE = "output_token_usage"
    DATE_CHANGE = "date_change"
    DEFERRED_TOOLS_DELTA = "deferred_tools_delta"
    AGENT_LISTING_DELTA = "agent_listing_delta"
    MCP_INSTRUCTIONS_DELTA = "mcp_instructions_delta"


@dataclass
class FileAttachment:
    """文件附件"""
    type: str = "file"
    filename: str = ""
    content: dict = field(default_factory=dict)
    truncated: bool = False
    display_path: str = ""


@dataclass
class TodoReminderAttachment:
    """待办提醒附件"""
    type: str = "todo_reminder"
    content: list = field(default_factory=list)
    item_count: int = 0


@dataclass
class TaskReminderAttachment:
    """任务提醒附件"""
    type: str = "task_reminder"
    content: list = field(default_factory=list)
    item_count: int = 0


@dataclass
class RelevantMemory:
    """相关记忆"""
    path: str
    content: str
    mtime_ms: int
    header: str = ""
    limit: Optional[int] = None


@dataclass
class RelevantMemoriesAttachment:
    """相关记忆附件"""
    type: str = "relevant_memories"
    memories: list[RelevantMemory] = field(default_factory=list)


@dataclass
class DiagnosticsAttachment:
    """诊断附件"""
    type: str = "diagnostics"
    files: list = field(default_factory=list)
    is_new: bool = True


@dataclass
class QueuedCommandAttachment:
    """队列命令附件"""
    type: str = "queued_command"
    prompt: str = ""
    source_uuid: Optional[str] = None
    image_paste_ids: list = field(default_factory=list)


@dataclass
class AgentMentionAttachment:
    """Agent提及附件"""
    type: str = "agent_mention"
    agent_type: str = ""


@dataclass
class McpResourceAttachment:
    """MCP资源附件"""
    type: str = "mcp_resource"
    server: str = ""
    uri: str = ""
    name: str = ""
    description: Optional[str] = None
    content: dict = field(default_factory=dict)


# 附件联合类型
Attachment = (
    FileAttachment 
    | TodoReminderAttachment 
    | TaskReminderAttachment 
    | RelevantMemoriesAttachment 
    | DiagnosticsAttachment 
    | QueuedCommandAttachment 
    | AgentMentionAttachment 
    | McpResourceAttachment 
    | dict
)


class AttachmentProcessor:
    """
    附件处理器
    
    负责从用户输入和上下文中提取并生成各种附件。
    """
    
    def __init__(self):
        self.loaded_nested_memory_paths: set = set()
        self.nested_memory_attachment_triggers: set = set()
        self.dynamic_skill_dir_triggers: set = set()
    
    @staticmethod
    def extract_at_mentioned_files(content: str) -> list[str]:
        """
        从文本中提取@提及的文件
        
        支持格式：
        - @file.txt
        - @file.txt#L10-20
        - @"my file.txt" (带空格的文件名)
        """
        results = []
        
        # 提取引号包围的文件名
        quoted_pattern = r'(?:^|\s)@"([^"]+)"'
        for match in re.finditer(quoted_pattern, content):
            filename = match.group(1)
            # 跳过agent提及
            if not filename.endswith(' (agent)'):
                results.append(filename)
        
        # 提取普通@提及
        # 匹配 @word 但排除 @agent-xxx 格式的agent提及
        unquoted_pattern = r'(?:^|\s)@([^\s]+)\b'
        for match in re.finditer(unquoted_pattern, content):
            filename = match.group(1)
            # 跳过引号包围的（已处理）
            if filename.startswith('"'):
                continue
            # 跳过agent提及
            if filename.startswith('agent-'):
                continue
            results.append(filename)
        
        return list(set(results))  # 去重
    
    @staticmethod
    def extract_agent_mentions(content: str) -> list[str]:
        """
        提取agent提及
        
        支持格式：
        - @agent-code-reviewer
        - @"code-reviewer (agent)"
        """
        results = []
        
        # 提取引号格式: @"<type> (agent)"
        quoted_pattern = r'(?:^|\s)@"([\w:.@-]+) \(agent\)"'
        for match in re.finditer(quoted_pattern, content):
            if match.group(1):
                results.append(match.group(1))
        
        # 提取无引号格式: @agent-<type>
        unquoted_pattern = r'(?:^|\s)@(agent-[\w:.@-]+)'
        for match in re.finditer(unquoted_pattern, content):
            results.append(match.group(1))
        
        return list(set(results))
    
    @staticmethod
    def extract_mcp_resource_mentions(content: str) -> list[str]:
        """
        提取MCP资源提及
        
        格式: @server:uri
        """
        pattern = r'(?:^|\s)@([^\s]+:[^\s]+)\b'
        return [m for m in re.findall(pattern, content)]
    
    @staticmethod
    def parse_at_mentioned_file_lines(mention: str) -> dict:
        """
        解析@提及的文件行号信息
        
        解析 "file.txt#L10-20" -> {"filename": "file.txt", "line_start": 10, "line_end": 20}
        """
        # 匹配 #L10-20 或 #L10 格式
        pattern = r'^([^#]+)(?:#L(\d+)(?:-(\d+))?)?(?:#[^#]*)?$'
        match = re.match(pattern, mention)
        
        if not match:
            return {"filename": mention}
        
        filename = match.group(1) or mention
        line_start_str = match.group(2)
        line_end_str = match.group(3)
        
        line_start = int(line_start_str) if line_start_str else None
        line_end = int(line_end_str) if line_end_str else line_start
        
        return {"filename": filename, "line_start": line_start, "line_end": line_end}
    
    async def process_at_mentioned_files(
        self,
        content: str,
        file_reader: callable,
    ) -> list[dict]:
        """
        处理@提及的文件
        
        Args:
            content: 用户输入文本
            file_reader: 文件读取函数，签名为 (filename, offset, limit) -> content
            
        Returns:
            文件附件列表
        """
        files = self.extract_at_mentioned_files(content)
        if not files:
            return []
        
        results = []
        for file_mention in files:
            try:
                parsed = self.parse_at_mentioned_file_lines(file_mention)
                filename = parsed["filename"]
                offset = parsed.get("line_start")
                limit = None
                
                if offset and parsed.get("line_end"):
                    limit = parsed["line_end"] - offset + 1
                
                # 读取文件
                file_content = await file_reader(filename, offset, limit)
                
                results.append({
                    "type": "file",
                    "filename": filename,
                    "content": file_content,
                    "displayPath": filename,
                    "truncated": False,
                })
                
            except Exception as e:
                log_error(f"Failed to read @-mentioned file {file_mention}: {e}")
        
        return results
    
    async def process_agent_mentions(
        self,
        content: str,
        available_agents: list[dict],
    ) -> list[dict]:
        """
        处理agent提及
        
        Args:
            content: 用户输入文本
            available_agents: 可用的agent定义列表
            
        Returns:
            Agent提及附件列表
        """
        mentions = self.extract_agent_mentions(content)
        if not mentions:
            return []
        
        agent_types = {a.get("agentType", "") for a in available_agents}
        
        results = []
        for mention in mentions:
            # 提取agent类型（移除agent-前缀）
            agent_type = mention.replace("agent-", "")
            
            if agent_type in agent_types:
                results.append({
                    "type": "agent_mention",
                    "agentType": agent_type,
                })
        
        return results
    
    def build_memory_header(self, path: str, mtime_ms: int) -> str:
        """
        构建记忆文件的头部字符串
        
        Args:
            path: 记忆文件路径
            mtime_ms: 修改时间戳
            
        Returns:
            格式化的头部字符串
        """
        from datetime import datetime, timezone, timedelta
        
        now_ms = datetime.now(timezone.utc).timestamp() * 1000
        age_ms = now_ms - mtime_ms
        age_hours = age_ms / (1000 * 60 * 60)
        
        if age_hours < 1:
            staleness = "Recently saved"
        elif age_hours < 24:
            staleness = f"Saved {int(age_hours)} hours ago"
        elif age_hours < 48:
            staleness = "Saved yesterday"
        else:
            days = int(age_hours / 24)
            staleness = f"Saved {days} days ago"
        
        return f"{staleness}\n\nMemory: {path}:"
    
    async def generate_attachments(
        self,
        input_text: Optional[str],
        context: dict,
        file_reader: Optional[callable] = None,
        available_agents: Optional[list[dict]] = None,
    ) -> list[dict]:
        """
        生成附件的主函数
        
        Args:
            input_text: 用户输入文本
            context: 上下文信息
            file_reader: 文件读取函数
            available_agents: 可用的agent列表
            
        Returns:
            附件列表
        """
        attachments = []
        
        # 1. 处理@提及的文件
        if input_text and file_reader:
            file_attachments = await self.process_at_mentioned_files(
                input_text, file_reader
            )
            attachments.extend(file_attachments)
        
        # 2. 处理agent提及
        if input_text and available_agents:
            agent_attachments = await self.process_agent_mentions(
                input_text, available_agents
            )
            attachments.extend(agent_attachments)
        
        # 3. TODO提醒
        todos = context.get("todos", [])
        if todos:
            attachments.append({
                "type": "todo_reminder",
                "content": todos,
                "itemCount": len(todos),
            })
        
        # 4. 任务提醒
        tasks = context.get("tasks", [])
        if tasks:
            attachments.append({
                "type": "task_reminder",
                "content": tasks,
                "itemCount": len(tasks),
            })
        
        # 5. 诊断信息
        diagnostics = context.get("diagnostics", [])
        if diagnostics:
            attachments.append({
                "type": "diagnostics",
                "files": diagnostics,
                "isNew": True,
            })
        
        # 6. Token使用情况
        token_usage = context.get("token_usage")
        if token_usage:
            attachments.append({
                "type": "token_usage",
                **token_usage,
            })
        
        return attachments


def create_attachment_message(attachment: dict) -> dict:
    """
    创建附件消息
    
    Args:
        attachment: 附件数据
        
    Returns:
        格式化的附件消息
    """
    import uuid
    return {
        "attachment": attachment,
        "type": "attachment",
        "uuid": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
    }


def filter_attachments_by_type(
    attachments: list[dict],
    types: list[str],
) -> list[dict]:
    """
    按类型过滤附件
    
    Args:
        attachments: 附件列表
        types: 要保留的类型列表
        
    Returns:
        过滤后的附件列表
    """
    return [a for a in attachments if a.get("type") in types]


# 导出
__all__ = [
    "AttachmentType",
    "FileAttachment",
    "TodoReminderAttachment",
    "TaskReminderAttachment",
    "RelevantMemory",
    "RelevantMemoriesAttachment",
    "DiagnosticsAttachment",
    "QueuedCommandAttachment",
    "AgentMentionAttachment",
    "McpResourceAttachment",
    "AttachmentProcessor",
    "create_attachment_message",
    "filter_attachments_by_type",
    "MAX_MEMORY_LINES",
    "MAX_MEMORY_BYTES",
    "MAX_SESSION_BYTES",
]
