"""
Task - 任务
基于 Claude Code task.ts 设计

任务管理工具。
"""
from typing import Callable, List, Optional, Any
from enum import Enum


class Status(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"


class Task:
    """
    任务
    """
    
    def __init__(self, id: str, name: str, fn: Callable = None):
        """
        Args:
            id: 任务ID
            name: 任务名称
            fn: 执行函数
        """
        self._id = id
        self._name = name
        self._fn = fn
        self._status = Status.PENDING
        self._result: Any = None
        self._error: Exception = None
        self._dependents: List["Task"] = []
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def status(self) -> Status:
        return self._status
    
    @property
    def result(self) -> Any:
        return self._result
    
    @property
    def error(self) -> Exception:
        return self._error
    
    def run(self) -> Any:
        """执行任务"""
        self._status = Status.RUNNING
        try:
            if self._fn:
                self._result = self._fn()
            self._status = Status.SUCCESS
            return self._result
        except Exception as e:
            self._error = e
            self._status = Status.FAILURE
            raise
    
    def cancel(self) -> None:
        """取消任务"""
        self._status = Status.CANCELLED
    
    def depends_on(self, task: "Task") -> "Task":
        """设置依赖"""
        self._dependents.append(task)
        return self


class TaskGroup:
    """
    任务组
    """
    
    def __init__(self, name: str = ""):
        """
        Args:
            name: 组名称
        """
        self._name = name
        self._tasks: List[Task] = []
    
    def add(self, id: str, name: str, fn: Callable = None) -> Task:
        """
        添加任务
        
        Args:
            id: 任务ID
            name: 任务名称
            fn: 执行函数
            
        Returns:
            Task实例
        """
        task = Task(id, name, fn)
        self._tasks.append(task)
        return task
    
    def get(self, id: str) -> Optional[Task]:
        """获取任务"""
        for task in self._tasks:
            if task.id == id:
                return task
        return None
    
    def run_all(self) -> List[Any]:
        """
        运行所有任务
        
        Returns:
            结果列表
        """
        results = []
        for task in self._tasks:
            task.run()
            results.append(task.result)
        return results
    
    def run_parallel(self, max_concurrent: int = 3) -> List[Any]:
        """
        并行运行任务
        
        Args:
            max_concurrent: 最大并发数
            
        Returns:
            结果列表
        """
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {executor.submit(task.run): task for task in self._tasks}
            results = []
            
            for future in concurrent.futures.as_completed(futures):
                task = futures[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append(e)
            
            return results
    
    @property
    def tasks(self) -> List[Task]:
        return list(self._tasks)
    
    def clear(self) -> None:
        """清空任务"""
        self._tasks.clear()


# 导出
__all__ = [
    "Status",
    "Task",
    "TaskGroup",
]
