"""
Schedule - 调度
基于 Claude Code schedule.ts 设计

定时调度工具。
"""
import time
from datetime import datetime, timedelta
from typing import Callable, List, Optional


class Job:
    """
    定时任务
    """
    
    def __init__(
        self,
        fn: Callable,
        interval: float = None,
        times: int = None,
        immediate: bool = False
    ):
        """
        Args:
            fn: 执行函数
            interval: 间隔（秒）
            times: 执行次数（None无限）
            immediate: 是否立即执行第一次
        """
        self._fn = fn
        self._interval = interval
        self._times = times
        self._immediate = immediate
        self._count = 0
        self._running = False
        self._last_run: float = None
    
    @property
    def count(self) -> int:
        return self._count
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    def should_run(self) -> bool:
        """是否应该运行"""
        if self._times and self._count >= self._times:
            return False
        
        if self._last_run is None:
            return True
        
        if self._immediate and self._count == 0:
            return True
        
        if self._interval:
            return time.time() - self._last_run >= self._interval
        
        return False
    
    def execute(self) -> None:
        """执行"""
        self._running = True
        try:
            self._fn()
        finally:
            self._running = False
            self._count += 1
            self._last_run = time.time()
    
    def reset(self) -> None:
        """重置"""
        self._count = 0
        self._last_run = None


class Scheduler:
    """
    调度器
    """
    
    def __init__(self):
        self._jobs: List[Job] = []
        self._running = False
    
    def add(
        self,
        fn: Callable,
        interval: float = None,
        times: int = None,
        immediate: bool = False
    ) -> Job:
        """
        添加任务
        
        Args:
            fn: 执行函数
            interval: 间隔
            times: 执行次数
            immediate: 立即执行
            
        Returns:
            Job实例
        """
        job = Job(fn, interval, times, immediate)
        self._jobs.append(job)
        return job
    
    def remove(self, job: Job) -> bool:
        """移除任务"""
        if job in self._jobs:
            self._jobs.remove(job)
            return True
        return False
    
    def run_once(self) -> None:
        """运行一次检查"""
        for job in self._jobs:
            if job.should_run():
                job.execute()
    
    def run(self, duration: float = None) -> None:
        """
        运行调度器
        
        Args:
            duration: 持续时间（秒）
        """
        self._running = True
        start = time.time()
        
        while self._running:
            if duration and (time.time() - start) >= duration:
                break
            
            self.run_once()
            time.sleep(0.1)
    
    def stop(self) -> None:
        """停止"""
        self._running = False
    
    @property
    def jobs(self) -> List[Job]:
        return list(self._jobs)


# 便捷函数
def every(interval: float) -> Job:
    """
    每隔一段时间执行
    
    Args:
        interval: 间隔（秒）
    """
    def decorator(fn: Callable) -> Job:
        return Job(fn, interval=interval)
    return decorator


def twice(fn: Callable) -> Job:
    """执行两次"""
    return Job(fn, times=2)


def once(fn: Callable) -> Job:
    """执行一次"""
    return Job(fn, times=1, immediate=True)


# 导出
__all__ = [
    "Job",
    "Scheduler",
    "every",
    "twice",
    "once",
]
