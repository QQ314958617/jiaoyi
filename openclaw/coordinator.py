"""
Coordinator - 多Agent协调器
从 Claude Code src/coordinator/coordinatorMode.ts 移植

核心概念：
1. Coordinator（协调者）- 主控Agent，理解用户需求，协调多个Worker
2. Worker（工作者）- 具体执行任务的子Agent
3. 通信机制：
   - spawn: 启动新Worker
   - send: 继续Worker
   - stop: 停止Worker
   - task_notification: 接收Worker结果

工作流程：
1. Research（研究阶段）- Worker并行研究
2. Synthesis（综合阶段）- Coordinator理解研究结果，写出实现规格
3. Implementation（实现阶段）- Worker执行实现
4. Verification（验证阶段）- Worker验证代码
"""
import threading
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime
import json


# ============================================================================
# Worker定义
# ============================================================================

class WorkerStatus(str, Enum):
    """Worker状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class WorkerSubagentType(str, Enum):
    """Worker子代理类型"""
    WORKER = "worker"           # 普通Worker
    COORDINATOR = "coordinator"  # 主协调者


@dataclass
class Worker:
    """Worker定义"""
    id: str
    name: str
    description: str
    subagent_type: WorkerSubagentType = WorkerSubagentType.WORKER
    status: WorkerStatus = WorkerStatus.PENDING
    prompt: str = ""
    result: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    parent_id: Optional[str] = None  # 父级Worker ID（用于继续）

    def duration_ms(self) -> int:
        end = self.completed_at or datetime.now()
        return int((end - self.created_at).total_seconds() * 1000)


# ============================================================================
# Coordinator状态
# ============================================================================

@dataclass
class CoordinatorState:
    """Coordinator状态"""
    workers: Dict[str, Worker] = field(default_factory=dict)
    pending_notifications: List[dict] = field(default_factory=list)
    log: List[str] = field(default_factory=list)


# ============================================================================
# Coordinator
# ============================================================================

class Coordinator:
    """
    多Agent协调器

    用法：
    1. 创建Coordinator
    2. 注册回调函数
    3. spawn() 启动Worker并行执行
    4. on_notification() 接收Worker结果
    5. send() 继续Worker执行
    6. stop() 停止Worker
    """

    def __init__(self, name: str = "Coordinator"):
        self.name = name
        self.state = CoordinatorState()
        self._lock = threading.Lock()
        self._callbacks: Dict[str, List[Callable]] = {
            "worker_started": [],
            "worker_completed": [],
            "worker_failed": [],
            "worker_stopped": [],
            "notification": [],
        }

    # ==================== Worker管理 ====================

    def spawn(
        self,
        description: str,
        prompt: str,
        subagent_type: WorkerSubagentType = WorkerSubagentType.WORKER,
        parent_id: Optional[str] = None,
    ) -> str:
        """
        启动新Worker
        返回 worker_id
        """
        worker_id = f"agent-{uuid.uuid4().hex[:8]}"

        worker = Worker(
            id=worker_id,
            name=description,
            description=description,
            subagent_type=subagent_type,
            prompt=prompt,
            parent_id=parent_id,
        )

        with self._lock:
            self.state.workers[worker_id] = worker

        self._emit("worker_started", worker)
        self._log(f"启动Worker: {description} ({worker_id})")

        # 启动Worker执行（这里简化处理，实际需要Agent执行环境）
        self._execute_worker(worker_id)

        return worker_id

    def send(
        self,
        to: str,
        message: str,
    ) -> bool:
        """
        继续Worker执行
        用于：
        - Worker完成后继续执行新任务
        - 修正Worker的错误
        """
        with self._lock:
            worker = self.state.workers.get(to)
            if not worker:
                self._log(f"Send失败: 未知worker {to}")
                return False

            # 更新prompt（追加新消息）
            worker.prompt = message
            worker.status = WorkerStatus.RUNNING
            worker.completed_at = None

        self._log(f"继续Worker {to}: {message[:50]}...")
        self._execute_worker(to)
        return True

    def stop(self, task_id: str) -> bool:
        """
        停止Worker
        """
        with self._lock:
            worker = self.state.workers.get(task_id)
            if not worker:
                return False

            worker.status = WorkerStatus.STOPPED
            worker.completed_at = datetime.now()

        self._emit("worker_stopped", worker)
        self._log(f"停止Worker: {task_id}")
        return True

    # ==================== 结果处理 ====================

    def complete(self, worker_id: str, result: str) -> None:
        """
        Worker执行完成（由外部调用）
        """
        with self._lock:
            worker = self.state.workers.get(worker_id)
            if not worker:
                return
            worker.status = WorkerStatus.COMPLETED
            worker.result = result
            worker.completed_at = datetime.now()

        self._emit("worker_completed", worker)
        self._log(f"Worker完成: {worker_id}")

    def fail(self, worker_id: str, error: str) -> None:
        """
        Worker执行失败（由外部调用）
        """
        with self._lock:
            worker = self.state.workers.get(worker_id)
            if not worker:
                return
            worker.status = WorkerStatus.FAILED
            worker.result = error
            worker.completed_at = datetime.now()

        self._emit("worker_failed", worker)
        self._log(f"Worker失败: {worker_id} - {error}")

    def on_notification(self, notification: dict) -> None:
        """
        处理task-notification
        格式：
        <task-notification>
        <task-id>{agentId}</task-id>
        <status>completed|failed|killed</status>
        <summary>{summary}</summary>
        <result>{result}</result>
        </task-notification>
        """
        task_id = notification.get("task_id") or notification.get("taskId")
        status = notification.get("status")
        summary = notification.get("summary", "")
        result = notification.get("result", "")

        if status == "completed":
            self.complete(task_id, result)
        elif status == "failed":
            self.fail(task_id, summary)
        elif status == "killed":
            self.stop(task_id)

        self._emit("notification", notification)

    # ==================== 查询 ====================

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        """获取Worker"""
        with self._lock:
            return self.state.workers.get(worker_id)

    def list_workers(
        self,
        status: Optional[WorkerStatus] = None,
    ) -> List[Worker]:
        """列出Worker"""
        with self._lock:
            workers = list(self.state.workers.values())
        if status:
            workers = [w for w in workers if w.status == status]
        return workers

    def running_workers(self) -> List[Worker]:
        """获取运行中的Worker"""
        return self.list_workers(WorkerStatus.RUNNING)

    def completed_workers(self) -> List[Worker]:
        """获取已完成的Worker"""
        return self.list_workers(WorkerStatus.COMPLETED)

    def synthesize_results(self) -> str:
        """
        综合所有Worker的结果
        Coordinator的核心职责：理解Worker结果，形成完整报告
        """
        results = []
        for worker in self.completed_workers():
            results.append({
                "name": worker.description,
                "result": worker.result,
                "duration_ms": worker.duration_ms(),
            })

        if not results:
            return "No results to synthesize."

        summary = f"综合 {len(results)} 个Worker结果:\n\n"
        for r in results:
            summary += f"## {r['name']}\n{r['result']}\n\n"
        return summary

    # ==================== 回调 ====================

    def on(
        self,
        event: str,
        callback: Callable,
    ) -> None:
        """注册回调"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, *args) -> None:
        """触发回调"""
        for cb in self._callbacks.get(event, []):
            try:
                cb(*args)
            except Exception as e:
                print(f"[Coordinator] Callback error: {e}")

    # ==================== 日志 ====================

    def _log(self, message: str) -> None:
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.state.log.append(log_entry)
        print(f"[Coordinator] {log_entry}")

    def get_log(self) -> List[str]:
        """获取日志"""
        with self._lock:
            return list(self.state.log)


# ============================================================================
# 简化的Worker执行器（用于演示）
# ============================================================================

def simple_worker_executor(coordinator: Coordinator, worker_id: str, prompt: str):
    """
    简单的Worker执行器（演示用）
    实际应该启动Agent执行
    """
    import time
    time.sleep(1)  # 模拟执行

    # 模拟一些结果
    result = f"Worker {worker_id} 执行完成。\nPrompt: {prompt}\n结论: 这是一个模拟结果。"
    coordinator.complete(worker_id, result)


# ============================================================================
# Coordinator实例方法扩展（让spawn更简单）
# ============================================================================

class AgentTool:
    """模拟AgentTool - 启动Worker"""

    def __init__(self, coordinator: Coordinator):
        self.coordinator = coordinator

    def __call__(
        self,
        description: str,
        prompt: str,
        subagent_type: str = "worker",
    ) -> dict:
        """启动Worker"""
        subagent_type_enum = (
            WorkerSubagentType.COORDINATOR
            if subagent_type == "coordinator"
            else WorkerSubagentType.WORKER
        )

        worker_id = self.coordinator.spawn(
            description=description,
            prompt=prompt,
            subagent_type=subagent_type_enum,
        )

        # 在新线程中执行
        thread = threading.Thread(
            target=simple_worker_executor,
            args=(self.coordinator, worker_id, prompt),
            daemon=True,
        )
        thread.start()

        return {"task_id": worker_id}


class SendMessageTool:
    """模拟SendMessageTool - 继续Worker"""

    def __init__(self, coordinator: Coordinator):
        self.coordinator = coordinator

    def __call__(self, to: str, message: str) -> dict:
        """继续Worker"""
        success = self.coordinator.send(to, message)
        return {"success": success}
