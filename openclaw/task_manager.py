"""
Task Manager - 任务管理器
从 Claude Code src/utils/task/framework.ts 移植
负责任务注册、状态更新、生命周期管理
"""
import os
import threading
import time
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from task_base import (
    TaskType,
    TaskStatus,
    is_terminal_status,
    generate_task_id,
    get_task_output_path,
)


@dataclass
class TaskState:
    """任务状态（存储在内存中）"""
    id: str
    type: TaskType
    status: TaskStatus
    description: str
    tool_use_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_paused_ms: int = 0
    output_file: str = ""
    output_offset: int = 0
    notified: bool = False
    # 扩展字段（用于特定任务类型）
    extra: Dict[str, Any] = field(default_factory=dict)

    def is_terminal(self) -> bool:
        return is_terminal_status(self.status)

    def duration_ms(self) -> int:
        """计算任务执行时长（毫秒）"""
        end = self.end_time or datetime.now()
        return int((end - self.start_time).total_seconds() * 1000)


class TaskCallbacks:
    """任务回调函数集合"""
    def __init__(self):
        self.on_start: List[Callable[[TaskState], None]] = []
        self.on_update: List[Callable[[TaskState], None]] = []
        self.on_complete: List[Callable[[TaskState], None]] = []
        self.on_fail: List[Callable[[TaskState], None]] = []
        self.on_kill: List[Callable[[TaskState], None]] = []


class TaskManager:
    """
    任务管理器 - 核心组件
    - 线程安全
    - 支持任务注册、更新、查询
    - 支持回调通知
    - 支持任务输出持久化
    """
    _instance: Optional["TaskManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self._tasks: Dict[str, TaskState] = {}
        self._callbacks = TaskCallbacks()
        self._rwlock = threading.RLock()

    @classmethod
    def get_instance(cls) -> "TaskManager":
        """获取单例实例"""
        return cls()

    # ==================== 任务注册 ====================

    def create_task(
        self,
        task_type: TaskType,
        description: str,
        tool_use_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> TaskState:
        """创建新任务"""
        tid = task_id or generate_task_id(task_type)
        task = TaskState(
            id=tid,
            type=task_type,
            status=TaskStatus.PENDING,
            description=description,
            tool_use_id=tool_use_id,
            output_file=get_task_output_path(tid),
        )
        self.register(task)
        return task

    def register(self, task: TaskState) -> None:
        """注册任务"""
        with self._rwlock:
            self._tasks[task.id] = task
        self._emit(self._callbacks.on_start, task)

    # ==================== 任务更新 ====================

    def update(self, task_id: str, updater: Callable[[TaskState], TaskState]) -> bool:
        """
        更新任务状态
        updater: 接收旧状态，返回新状态
        返回: 是否更新成功
        """
        with self._rwlock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            new_task = updater(task)
            if new_task is task:
                return True  # 没有变化
            self._tasks[task_id] = new_task
            task = new_task

        # 触发回调
        self._emit(self._callbacks.on_update, task)
        if is_terminal_status(task.status):
            if task.status == TaskStatus.COMPLETED:
                self._emit(self._callbacks.on_complete, task)
            elif task.status == TaskStatus.FAILED:
                self._emit(self._callbacks.on_fail, task)
            elif task.status == TaskStatus.KILLED:
                self._emit(self._callbacks.on_kill, task)

        return True

    def set_status(self, task_id: str, status: TaskStatus) -> bool:
        """快捷方法：设置任务状态"""
        return self.update(task_id, lambda t: self._update_status(t, status))

    def _update_status(self, task: TaskState, status: TaskStatus) -> TaskState:
        """更新状态并设置结束时间"""
        update = {"status": status}
        if is_terminal_status(status) and task.end_time is None:
            update["end_time"] = datetime.now()
        return self._merge_task(task, update)

    def _merge_task(self, task: TaskState, updates: Dict[str, Any]) -> TaskState:
        """合并更新到任务"""
        task_dict = {**task.__dict__, **updates}
        return TaskState(**task_dict)

    # ==================== 任务操作 ====================

    def start(self, task_id: str) -> bool:
        """启动任务"""
        return self.set_status(task_id, TaskStatus.RUNNING)

    def complete(self, task_id: str) -> bool:
        """完成任务"""
        return self.set_status(task_id, TaskStatus.COMPLETED)

    def fail(self, task_id: str) -> bool:
        """标记任务失败"""
        return self.set_status(task_id, TaskStatus.FAILED)

    def kill(self, task_id: str) -> bool:
        """终止任务"""
        return self.set_status(task_id, TaskStatus.KILLED)

    # ==================== 任务查询 ====================

    def get(self, task_id: str) -> Optional[TaskState]:
        """获取任务"""
        with self._rwlock:
            return self._tasks.get(task_id)

    def list(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
    ) -> List[TaskState]:
        """列出任务"""
        with self._rwlock:
            tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if task_type:
            tasks = [t for t in tasks if t.type == task_type]
        return tasks

    def running_tasks(self) -> List[TaskState]:
        """获取所有运行中的任务"""
        return self.list(status=TaskStatus.RUNNING)

    def terminal_tasks(self) -> List[TaskState]:
        """获取所有已结束的任务"""
        with self._rwlock:
            return [t for t in self._tasks.values() if t.is_terminal()]

    def non_terminal_tasks(self) -> List[TaskState]:
        """获取所有未结束的任务"""
        with self._rwlock:
            return [t for t in self._tasks.values() if not t.is_terminal()]

    # ==================== 任务输出 ====================

    def write_output(self, task_id: str, content: str, offset: bool = True) -> bool:
        """写入任务输出"""
        task = self.get(task_id)
        if not task:
            return False
        mode = "a" if offset else "w"
        with open(task.output_file, mode, encoding="utf-8") as f:
            f.write(content)
        if offset:
            self.update(task_id, lambda t: self._merge_task(t, {
                "output_offset": t.output_offset + len(content)
            }))
        return True

    def read_output(self, task_id: str, from_offset: int = 0) -> Optional[str]:
        """读取任务输出（从指定偏移开始）"""
        task = self.get(task_id)
        if not task:
            return None
        if not os.path.exists(task.output_file):
            return ""
        with open(task.output_file, "r", encoding="utf-8") as f:
            f.seek(from_offset)
            return f.read()

    # ==================== 回调系统 ====================

    def on_start(self, callback: Callable[[TaskState], None]) -> None:
        self._callbacks.on_start.append(callback)

    def on_update(self, callback: Callable[[TaskState], None]) -> None:
        self._callbacks.on_update.append(callback)

    def on_complete(self, callback: Callable[[TaskState], None]) -> None:
        self._callbacks.on_complete.append(callback)

    def on_fail(self, callback: Callable[[TaskState], None]) -> None:
        self._callbacks.on_fail.append(callback)

    def on_kill(self, callback: Callable[[TaskState], None]) -> None:
        self._callbacks.on_kill.append(callback)

    def _emit(self, callbacks: List[Callable], task: TaskState) -> None:
        for cb in callbacks:
            try:
                cb(task)
            except Exception as e:
                print(f"[TaskManager] Callback error: {e}")

    # ==================== 清理 ====================

    def cleanup_terminal(self, grace_ms: int = 3000) -> int:
        """
        清理已结束的任务（超时后）
        返回清理数量
        """
        now = datetime.now()
        cleaned = 0
        with self._rwlock:
            to_remove = []
            for task in self._tasks.values():
                if task.is_terminal() and task.end_time:
                    age_ms = (now - task.end_time).total_seconds() * 1000
                    if age_ms > grace_ms:
                        to_remove.append(task.id)
            for tid in to_remove:
                del self._tasks[tid]
                cleaned += 1
        return cleaned

    def stats(self) -> Dict[str, Any]:
        """获取任务统计"""
        with self._rwlock:
            tasks = list(self._tasks.values())
        return {
            "total": len(tasks),
            "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in tasks if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED),
            "killed": sum(1 for t in tasks if t.status == TaskStatus.KILLED),
        }


# 全局实例
task_manager = TaskManager.get_instance()
