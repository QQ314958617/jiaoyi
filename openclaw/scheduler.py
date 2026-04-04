"""
Scheduler - 调度器
基于 Claude Code scheduler.ts 设计

任务调度工具。
"""
import asyncio
import time
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class Task:
    """调度任务"""
    id: str
    func: Callable
    interval: float  # 秒
    enabled: bool = True


class Scheduler:
    """
    简单任务调度器
    
    定期执行任务。
    """
    
    def __init__(self):
        self._tasks: dict = {}
        self._running = False
        self._task = None
    
    def add_task(
        self,
        task_id: str,
        func: Callable,
        interval_seconds: float,
    ) -> None:
        """
        添加任务
        
        Args:
            task_id: 任务ID
            func: 要执行的函数
            interval_seconds: 执行间隔（秒）
        """
        self._tasks[task_id] = Task(
            id=task_id,
            func=func,
            interval=interval_seconds,
        )
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = True
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self._tasks:
            self._tasks[task_id].enabled = False
            return True
        return False
    
    async def start(self) -> None:
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
    
    async def stop(self) -> None:
        """停止调度器"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _run(self) -> None:
        """运行循环"""
        last_run = {task_id: 0 for task_id in self._tasks}
        
        while self._running:
            now = time.time()
            
            for task_id, task in self._tasks.items():
                if not task.enabled:
                    continue
                
                elapsed = now - last_run.get(task_id, 0)
                
                if elapsed >= task.interval:
                    try:
                        if asyncio.iscoroutinefunction(task.func):
                            asyncio.create_task(task.func())
                        else:
                            task.func()
                    except Exception:
                        pass
                    
                    last_run[task_id] = now
            
            await asyncio.sleep(0.1)  # 检查频率


class Interval:
    """
    间隔执行器
    
    简单的周期性执行。
    """
    
    def __init__(
        self,
        interval_seconds: float,
        func: Callable,
    ):
        """
        Args:
            interval_seconds: 间隔秒数
            func: 要执行的函数
        """
        self._interval = interval_seconds
        self._func = func
        self._running = False
        self._task = None
    
    async def start(self) -> None:
        """启动"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
    
    async def stop(self) -> None:
        """停止"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _run(self) -> None:
        """运行循环"""
        while self._running:
            try:
                if asyncio.iscoroutinefunction(self._func):
                    await self._func()
                else:
                    self._func()
            except Exception:
                pass
            
            await asyncio.sleep(self._interval)


# 导出
__all__ = [
    "Task",
    "Scheduler",
    "Interval",
]
