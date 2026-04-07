"""
Task System - 任务系统核心
从 Claude Code src/Task.ts 移植
"""
import os
import random
import string
from enum import Enum
from typing import Callable, Optional
from datetime import datetime


class TaskType(str, Enum):
    """任务类型枚举"""
    LOCAL_BASH = "local_bash"
    LOCAL_AGENT = "local_agent"
    REMOTE_AGENT = "remote_agent"
    IN_PROCESS_TEAMMATE = "in_process_teammate"
    LOCAL_WORKFLOW = "local_workflow"
    MONITOR_MCP = "monitor_mcp"
    DREAM = "dream"


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"


def is_terminal_status(status: TaskStatus) -> bool:
    """判断是否为终态（不会再转换）"""
    return status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED)


# 任务ID前缀映射
TASK_ID_PREFIXES = {
    TaskType.LOCAL_BASH: "b",
    TaskType.LOCAL_AGENT: "a",
    TaskType.REMOTE_AGENT: "r",
    TaskType.IN_PROCESS_TEAMMATE: "t",
    TaskType.LOCAL_WORKFLOW: "w",
    TaskType.MONITOR_MCP: "m",
    TaskType.DREAM: "d",
}

# 安全的字母表（避免歧义）
TASK_ID_ALPHABET = string.digits + string.ascii_lowercase


def generate_task_id(task_type: TaskType) -> str:
    """
    生成唯一任务ID
    格式: 前缀 + 8位随机字符
    示例: b1a2b3c4d, a9x8y7z6w
    """
    prefix = TASK_ID_PREFIXES.get(task_type, "x")
    random_bytes = os.urandom(8)
    suffix = "".join(TASK_ID_ALPHABET[b % len(TASK_ID_ALPHABET)] for b in random_bytes)
    return f"{prefix}{suffix}"


def get_task_output_path(task_id: str, base_dir: str = "/tmp/task_outputs") -> str:
    """获取任务输出文件路径"""
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, f"{task_id}.output")
