"""
LocalBashTask - 本地Shell任务执行器
从 Claude Code src/tasks/LocalShellTask/ 移植
展示如何实现具体任务类型
"""
import subprocess
import threading
import time
import uuid
from typing import Optional, Callable

from task_base import TaskType, get_task_output_path
from task_manager import task_manager, TaskState


# 等待输入检测间隔（毫秒）
STALL_CHECK_INTERVAL_MS = 5000
# 等待输入阈值（毫秒）
STALL_THRESHOLD_MS = 45000
# 读取尾字节数
STALL_TAIL_BYTES = 1024

# 交互提示模式
PROMPT_PATTERNS = [
    r"\(y\/n\)",
    r"\[y\/n\]",
    r"\(yes\/no\)",
    r"Do you\?|Would you\?|Shall I\?|Are you sure\?",
    r"Press (any key|Enter)",
    r"Continue\?|Overwrite\?",
]


def looks_like_prompt(tail: str) -> bool:
    """检查输出是否像交互式提示"""
    import re
    last_line = tail.strip().split("\n")[-1] if tail else ""
    return any(re.search(p, last_line, re.IGNORECASE) for p in PROMPT_PATTERNS)


class LocalBashTask:
    """
    本地Shell任务执行器

    功能：
    - 执行shell命令
    - 后台运行支持
    - 输出实时捕获
    - 卡住检测（等待输入）
    - 超时控制
    """

    def __init__(
        self,
        command: str,
        description: str = "",
        timeout: Optional[int] = None,
        task_id: Optional[str] = None,
        on_output: Optional[Callable[[str], None]] = None,
    ):
        self.command = command
        self.description = description or command[:50]
        self.timeout = timeout
        self.task_id = task_id or task_manager.create_task(
            TaskType.LOCAL_BASH,
            self.description,
        ).id
        self.on_output = on_output

        self._process: Optional[subprocess.Popen] = None
        self._cancel_event = threading.Event()
        self._output_lock = threading.Lock()
        self._stall_timer: Optional[threading.Timer] = None
        self._timeout_timer: Optional[threading.Timer] = None

    def run(self) -> tuple[int, str]:
        """
        执行命令并等待完成
        返回: (exit_code, output)
        """
        task_manager.start(self.task_id)

        # 启动输出监控线程
        output_collector = []
        stall_checker = self._start_stall_watcher()

        try:
            self._process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # 设置超时
            if self.timeout:
                self._timeout_timer = threading.Timer(self.timeout / 1000, self._handle_timeout)
                self._timeout_timer.start()

            # 实时读取输出
            for line in self._process.stdout:
                if self._cancel_event.is_set():
                    break
                output_collector.append(line)
                if self.on_output:
                    self.on_output(line)

                # 写入任务输出文件
                task_manager.write_output(self.task_id, line)

            self._process.wait()
            exit_code = self._process.returncode

        except Exception as e:
            task_manager.write_output(self.task_id, f"\n[ERROR] {e}\n")
            exit_code = -1
        finally:
            self._cleanup()
            if exit_code == 0:
                task_manager.complete(self.task_id)
            else:
                task_manager.fail(self.task_id)

        output = "".join(output_collector)
        return exit_code, output

    def run_bg(self) -> str:
        """
        后台执行命令（立即返回）
        返回 task_id
        """
        thread = threading.Thread(target=self._run_bg_wrapper, daemon=True)
        thread.start()
        return self.task_id

    def _run_bg_wrapper(self) -> None:
        """后台执行包装"""
        self.run()

    def kill(self) -> bool:
        """终止任务"""
        self._cancel_event.set()
        if self._process:
            try:
                self._process.terminate()
                time.sleep(0.1)
                if self._process.poll() is None:
                    self._process.kill()
            except Exception:
                pass
        return task_manager.kill(self.task_id)

    def _start_stall_watcher(self) -> Callable:
        """启动卡住检测"""
        def check():
            if self._cancel_event.is_set():
                return
            output = task_manager.read_output(self.task_id)
            if output and looks_like_prompt(output[-STALL_TAIL_BYTES:]):
                # 检测到可能等待输入
                if self.on_output:
                    self.on_output(f"\n[WARNING] Command may be waiting for input...\n")
                # 继续监控
                self._stall_timer = threading.Timer(
                    STALL_CHECK_INTERVAL_MS / 1000, check
                )
                self._stall_timer.start()

        self._stall_timer = threading.Timer(
            STALL_CHECK_INTERVAL_MS / 1000, check
        )
        self._stall_timer.start()
        return lambda: self._stall_timer.cancel() if self._stall_timer else None

    def _handle_timeout(self) -> None:
        """处理超时"""
        if self.on_output:
            self.on_output(f"\n[TIMEOUT] Command timed out after {self.timeout}ms\n")
        self.kill()

    def _cleanup(self) -> None:
        """清理资源"""
        if self._stall_timer:
            self._stall_timer.cancel()
        if self._timeout_timer:
            self._timeout_timer.cancel()


# 便捷函数
def run_bash(
    command: str,
    description: str = "",
    timeout: Optional[int] = None,
) -> tuple[int, str]:
    """执行bash命令（同步）"""
    task = LocalBashTask(command, description, timeout)
    return task.run()


def run_bash_bg(
    command: str,
    description: str = "",
) -> str:
    """执行bash命令（后台）"""
    task = LocalBashTask(command, description)
    return task.run_bg()


def kill_task(task_id: str) -> bool:
    """终止任务"""
    task = task_manager.get(task_id)
    if not task:
        return False
    if task.type == TaskType.LOCAL_BASH:
        # 这里简化处理，实际需要维护task_id->process的映射
        return task_manager.kill(task_id)
    return False
