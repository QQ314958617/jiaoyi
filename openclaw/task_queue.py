"""
OpenClaw Task Queue
===================
Inspired by Claude Code's src/utils/sdkEventQueue.ts.

任务队列 + 事件系统，支持：
1. 任务事件入队/出队
2. 任务状态跟踪（started/progress/completed/failed）
3. 最大队列限制（FIFO淘汰）
4. 任务生命周期管理

用途：
- 交易任务队列
- 异步任务处理
- 任务进度追踪
"""

from __future__ import annotations

import asyncio, threading, uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from queue import Queue, Empty

# ============================================================================
# 任务事件类型
# ============================================================================

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

@dataclass
class TaskEvent:
    """任务事件"""
    task_id: str
    subtype: str  # "task_started" | "task_progress" | "task_notification"
    description: str = ""
    status: Optional[TaskStatus] = None
    usage: Optional[Dict[str, Any]] = None  # total_tokens, tool_uses, duration_ms
    last_tool_name: Optional[str] = None
    summary: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

@dataclass
class Task:
    """任务"""
    task_id: str
    description: str
    task_type: str = "general"
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    usage: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def to_event(self, subtype: str) -> TaskEvent:
        return TaskEvent(
            task_id=self.task_id,
            subtype=subtype,
            description=self.description,
            status=self.status,
            usage=self.usage if self.usage else None,
            summary=self.summary if hasattr(self, 'summary') else None
        )

# ============================================================================
# 任务队列
# ============================================================================

class TaskQueue:
    """
    任务队列
    
    支持：
    - FIFO 队列
    - 最大容量限制
    - 任务状态跟踪
    - 事件通知
    """
    
    def __init__(self, max_size: int = 1000):
        self._queue: List[Task] = []
        self._events: List[TaskEvent] = []
        self._max_size = max_size
        self._lock = threading.Lock()
        self._task_index: Dict[str, Task] = {}
        self._subscribers: List[Callable] = []
    
    def enqueue(self, task: Task) -> str:
        """
        入队任务
        
        如果队列已满，淘汰最旧的任务
        """
        with self._lock:
            # 检查是否已存在
            if task.task_id in self._task_index:
                # 更新现有任务
                existing = self._task_index[task.task_id]
                for i, t in enumerate(self._queue):
                    if t.task_id == task.task_id:
                        self._queue[i] = task
                        break
            else:
                # 添加新任务
                if len(self._queue) >= self._max_size:
                    # 淘汰最旧任务
                    oldest = self._queue.pop(0)
                    del self._task_index[oldest.task_id]
                
                self._queue.append(task)
                self._task_index[task.task_id] = task
            
            # 记录事件
            event = task.to_event("task_started")
            self._events.append(event)
        
        # 通知订阅者
        self._notify(event)
        
        return task.task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        with self._lock:
            return self._task_index.get(task_id)
    
    def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        """更新任务状态"""
        with self._lock:
            if task_id not in self._task_index:
                return None
            
            task = self._task_index[task_id]
            
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            # 记录事件
            event = task.to_event("task_progress")
            self._events.append(event)
        
        self._notify(event)
        return task
    
    def complete_task(self, task_id: str, result: Any = None, 
                    error: Optional[str] = None, usage: Optional[Dict] = None) -> Optional[Task]:
        """标记任务完成"""
        with self._lock:
            if task_id not in self._task_index:
                return None
            
            task = self._task_index[task_id]
            task.status = TaskStatus.FAILED if error else TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            task.result = result
            task.error = error
            if usage:
                task.usage = usage
            
            # 记录完成事件
            event = TaskEvent(
                task_id=task_id,
                subtype="task_notification",
                description=task.description,
                status=task.status,
                usage=usage,
                summary=str(result) if result else error or ""
            )
            self._events.append(event)
        
        self._notify(event)
        return task
    
    def dequeue(self) -> Optional[Task]:
        """出队下一个待处理任务"""
        with self._lock:
            for task in self._queue:
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    
                    event = task.to_event("task_progress")
                    self._events.append(event)
                    self._notify(event)
                    
                    return task
            return None
    
    def peek(self, n: int = 10) -> List[Task]:
        """查看前 n 个任务"""
        with self._lock:
            return list(self._queue[:n])
    
    def get_events(self, since: Optional[str] = None) -> List[TaskEvent]:
        """获取事件（可按时间过滤）"""
        with self._lock:
            if since is None:
                return list(self._events)
            
            # 按时间过滤
            filtered = [e for e in self._events if e.timestamp >= since]
            return filtered
    
    def subscribe(self, callback: Callable[[TaskEvent], None]) -> Callable:
        """订阅任务事件"""
        with self._lock:
            self._subscribers.append(callback)
        
        def unsubscribe():
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)
        
        return unsubscribe
    
    def _notify(self, event: TaskEvent) -> None:
        """通知所有订阅者"""
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception:
                import traceback
                traceback.print_exc()
    
    def clear(self) -> None:
        """清空队列"""
        with self._lock:
            self._queue.clear()
            self._events.clear()
            self._task_index.clear()
    
    def size(self) -> int:
        """队列大小"""
        with self._lock:
            return len(self._queue)
    
    def pending_count(self) -> int:
        """待处理任务数"""
        with self._lock:
            return sum(1 for t in self._queue if t.status == TaskStatus.PENDING)
    
    def running_count(self) -> int:
        """运行中任务数"""
        with self._lock:
            return sum(1 for t in self._queue if t.status == TaskStatus.RUNNING)


# ============================================================================
# 全局任务队列实例
# ============================================================================

_task_queue: Optional[TaskQueue] = None
_queue_lock = threading.Lock()

def get_task_queue() -> TaskQueue:
    """获取全局任务队列"""
    global _task_queue
    with _queue_lock:
        if _task_queue is None:
            _task_queue = TaskQueue()
        return _task_queue

def create_task(description: str, task_type: str = "general") -> Task:
    """创建新任务"""
    task_id = str(uuid.uuid4())[:8]
    return Task(task_id=task_id, description=description, task_type=task_type)

def submit_task(description: str, task_type: str = "general") -> str:
    """提交任务到队列"""
    task = create_task(description, task_type)
    queue = get_task_queue()
    return queue.enqueue(task)
