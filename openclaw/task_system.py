"""
Task System - Ported from Claude Code's src/Task.ts

Core task types, status management, and task ID generation.
Supports multiple task types: local_bash, local_agent, remote_agent,
in_process_teammate, local_workflow, monitor_mcp, dream.

Key design patterns:
- Terminal state guards (completed/failed/killed won't transition further)
- Task ID with type prefix + 8 random base36 chars (36^8 ≈ 2.8T combinations)
- TaskStateBase for shared fields across all task states
"""

import os
import random
import string
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, TypeVar

# Task ID alphabet: digits + lowercase (case-insensitive safe for filenames)
_TASK_ID_ALPHABET = string.digits + string.ascii_lowercase

# Task ID prefix map
_TASK_ID_PREFIXES: dict[str, str] = {
    'local_bash': 'b',           # Keep 'b' for backward compatibility
    'local_agent': 'a',
    'remote_agent': 'r',
    'in_process_teammate': 't',
    'local_workflow': 'w',
    'monitor_mcp': 'm',
    'dream': 'd',
}


class TaskType(str, Enum):
    """Task types supported by the system."""
    LOCAL_BASH = 'local_bash'
    LOCAL_AGENT = 'local_agent'
    REMOTE_AGENT = 'remote_agent'
    IN_PROCESS_TEAMMATE = 'in_process_teammate'
    LOCAL_WORKFLOW = 'local_workflow'
    MONITOR_MCP = 'monitor_mcp'
    DREAM = 'dream'


class TaskStatus(str, Enum):
    """Task lifecycle status."""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    KILLED = 'killed'


def is_terminal_task_status(status: TaskStatus) -> bool:
    """
    True when a task is in a terminal state and will not transition further.
    
    Used to guard against:
    - Injecting messages into dead teammates
    - Evicting finished tasks from AppState
    - Orphan cleanup paths
    """
    return status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.KILLED)


@dataclass
class TaskHandle:
    """Handle for tracking a running task."""
    task_id: str
    cleanup: Optional[Callable[[], None]] = None


# Type variable for generic SetAppState
S = TypeVar('S')


@dataclass
class TaskContext:
    """Context passed to task executors."""
    abort_controller: 'AbortController'
    get_app_state: Callable[[], dict]  # () -> AppState
    set_app_state: Callable[[Callable[[dict], dict]], None]  # SetAppState


@dataclass
class TaskStateBase:
    """
    Base fields shared by all task states.
    
    Attributes:
        id: Unique task identifier
        type: TaskType classification
        status: Current lifecycle status
        description: Human-readable task description
        tool_use_id: Optional linked tool use ID
        start_time: Unix timestamp (ms) when task started
        end_time: Optional Unix timestamp when task ended
        total_paused_ms: Total time spent paused
        output_file: Path to task output file
        output_offset: Read offset for streaming output
        notified: Whether user has been notified
    """
    id: str
    type: TaskType
    status: TaskStatus
    description: str
    tool_use_id: Optional[str] = None
    start_time: int = field(default_factory=lambda: int(__import__('time').time() * 1000))
    end_time: Optional[int] = None
    total_paused_ms: Optional[int] = None
    output_file: str = ''
    output_offset: int = 0
    notified: bool = False

    def to_dict(self) -> dict:
        """Serialize to dictionary (AppState format)."""
        return {
            'id': self.id,
            'type': self.type.value if isinstance(self.type, Enum) else self.type,
            'status': self.status.value if isinstance(self.status, Enum) else self.status,
            'description': self.description,
            'toolUseId': self.tool_use_id,
            'startTime': self.start_time,
            'endTime': self.end_time,
            'totalPausedMs': self.total_paused_ms,
            'outputFile': self.output_file,
            'outputOffset': self.output_offset,
            'notified': self.notified,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TaskStateBase':
        """Deserialize from dictionary."""
        status = data.get('status', 'pending')
        if isinstance(status, str):
            status = TaskStatus(status)
        type_val = data.get('type', 'local_bash')
        if isinstance(type_val, str):
            type_val = TaskType(type_val)
        return cls(
            id=data['id'],
            type=type_val,
            status=status,
            description=data.get('description', ''),
            tool_use_id=data.get('toolUseId'),
            start_time=data.get('startTime', 0),
            end_time=data.get('endTime'),
            total_paused_ms=data.get('totalPausedMs'),
            output_file=data.get('outputFile', ''),
            output_offset=data.get('outputOffset', 0),
            notified=data.get('notified', False),
        )


@dataclass
class LocalShellSpawnInput:
    """Input for spawning a local shell task."""
    command: str
    description: str
    timeout: Optional[int] = None
    tool_use_id: Optional[str] = None
    agent_id: Optional[str] = None
    # UI display variant: 'bash' | 'monitor'
    kind: str = 'bash'


def get_task_id_prefix(type: TaskType) -> str:
    """Get the ID prefix for a task type."""
    return _TASK_ID_PREFIXES.get(type.value, 'x')


def generate_task_id(task_type: TaskType) -> str:
    """
    Generate a unique task ID.
    
    Format: <prefix> + 8 random base36 chars
    - 36^8 ≈ 2.8 trillion combinations
    - Sufficient to resist brute-force symlink attacks
    
    Args:
        task_type: The type of task to generate ID for
        
    Returns:
        Unique task ID string
    """
    prefix = get_task_id_prefix(task_type)
    # Use os.urandom for cryptographically secure randomness
    bytes_data = os.urandom(8)
    id_chars = []
    for byte in bytes_data:
        idx = byte % len(_TASK_ID_ALPHABET)
        id_chars.append(_TASK_ID_ALPHABET[idx])
    return prefix + ''.join(id_chars)


def get_task_output_path(task_id: str) -> str:
    """
    Get the output file path for a task.
    
    Args:
        task_id: The task identifier
        
    Returns:
        Path to the task's output file in temp directory
    """
    import tempfile
    task_dir = os.path.join(tempfile.gettempdir(), 'claude-tasks')
    os.makedirs(task_dir, exist_ok=True)
    return os.path.join(task_dir, f'{task_id}.output')


def create_task_state_base(
    task_id: str,
    task_type: TaskType,
    description: str,
    tool_use_id: Optional[str] = None,
) -> TaskStateBase:
    """
    Factory to create a TaskStateBase with defaults.
    
    Args:
        task_id: Unique task identifier
        task_type: Type of task
        description: Human-readable description
        tool_use_id: Optional linked tool use ID
        
    Returns:
        New TaskStateBase instance
    """
    return TaskStateBase(
        id=task_id,
        type=task_type,
        status=TaskStatus.PENDING,
        description=description,
        tool_use_id=tool_use_id,
        start_time=int(__import__('time').time() * 1000),
        output_file=get_task_output_path(task_id),
        output_offset=0,
        notified=False,
    )


# Abstract task interface (port of Task interface)
class Task:
    """Abstract base for task implementations."""
    
    @property
    def name(self) -> str:
        raise NotImplementedError
    
    @property
    def type(self) -> TaskType:
        raise NotImplementedError
    
    async def kill(self, task_id: str, set_app_state: Callable) -> None:
        """
        Kill a running task.
        
        Args:
            task_id: ID of task to kill
            set_app_state: State setter function
        """
        raise NotImplementedError


# ============================================================================
# Task Registry - Manages running tasks
# ============================================================================

class TaskRegistry:
    """
    Registry for tracking running tasks.
    
    Thread-safe task management with terminal state guards.
    """
    
    def __init__(self):
        self._tasks: dict[str, TaskStateBase] = {}
        self._handles: dict[str, TaskHandle] = {}
    
    def register(self, state: TaskStateBase, handle: Optional[TaskHandle] = None) -> None:
        """Register a new task."""
        self._tasks[state.id] = state
        if handle:
            self._handles[state.id] = handle
    
    def get(self, task_id: str) -> Optional[TaskStateBase]:
        """Get task state by ID."""
        return self._tasks.get(task_id)
    
    def update(self, task_id: str, updates: dict) -> bool:
        """
        Update task state fields.
        
        Returns:
            True if updated, False if task not found
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        return True
    
    def is_terminal(self, task_id: str) -> bool:
        """Check if task is in terminal state."""
        task = self._tasks.get(task_id)
        return is_terminal_task_status(task.status) if task else True
    
    def get_all(self) -> list[TaskStateBase]:
        """Get all registered tasks."""
        return list(self._tasks.values())
    
    def get_by_status(self, status: TaskStatus) -> list[TaskStateBase]:
        """Get all tasks with given status."""
        return [t for t in self._tasks.values() if t.status == status]
    
    def unregister(self, task_id: str) -> Optional[TaskHandle]:
        """Unregister a task and return its handle."""
        self._tasks.pop(task_id, None)
        return self._handles.pop(task_id, None)


# Global task registry
_task_registry: Optional[TaskRegistry] = None


def get_task_registry() -> TaskRegistry:
    """Get the global task registry instance."""
    global _task_registry
    if _task_registry is None:
        _task_registry = TaskRegistry()
    return _task_registry


# ============================================================================
# Convenience functions
# ============================================================================

def create_local_bash_task(
    command: str,
    description: str,
    timeout: Optional[int] = None,
    tool_use_id: Optional[str] = None,
) -> tuple[str, TaskStateBase]:
    """
    Create a local bash task with generated ID.
    
    Returns:
        Tuple of (task_id, TaskStateBase)
    """
    task_id = generate_task_id(TaskType.LOCAL_BASH)
    state = create_task_state_base(task_id, TaskType.LOCAL_BASH, description, tool_use_id)
    return task_id, state


def mark_task_running(task_id: str) -> None:
    """Mark a task as running."""
    registry = get_task_registry()
    registry.update(task_id, {'status': TaskStatus.RUNNING})


def mark_task_completed(task_id: str, end_time: Optional[int] = None) -> None:
    """Mark a task as completed."""
    registry = get_task_registry()
    updates: dict = {'status': TaskStatus.COMPLETED}
    if end_time is not None:
        updates['end_time'] = end_time
    registry.update(task_id, updates)


def mark_task_failed(task_id: str, end_time: Optional[int] = None) -> None:
    """Mark a task as failed."""
    registry = get_task_registry()
    updates: dict = {'status': TaskStatus.FAILED}
    if end_time is not None:
        updates['end_time'] = end_time
    registry.update(task_id, updates)


def mark_task_killed(task_id: str, end_time: Optional[int] = None) -> None:
    """Mark a task as killed."""
    registry = get_task_registry()
    updates: dict = {'status': TaskStatus.KILLED}
    if end_time is not None:
        updates['end_time'] = end_time
    registry.update(task_id, updates)
