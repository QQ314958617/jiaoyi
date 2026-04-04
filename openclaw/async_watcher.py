"""
AsyncWatcher - 异步监控
基于 Claude Code asyncWatcher.ts 设计

异步资源监控。
"""
import asyncio
import time
from typing import Callable, Dict, List, Optional


class AsyncWatcher:
    """
    异步监控器
    
    监控资源状态。
    """
    
    def __init__(
        self,
        check_interval_ms: int = 5000,
    ):
        """
        Args:
            check_interval_ms: 检查间隔毫秒
        """
        self._check_interval_ms = check_interval_ms
        self._resources: Dict[str, dict] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def register(
        self,
        name: str,
        check_fn: Callable[[], bool],
        on_failure: Callable = None,
    ) -> None:
        """
        注册监控资源
        
        Args:
            name: 资源名
            check_fn: 检查函数
            on_failure: 失败回调
        """
        self._resources[name] = {
            "check_fn": check_fn,
            "status": "unknown",
            "last_check": None,
            "failure_count": 0,
        }
        
        if on_failure:
            if name not in self._callbacks:
                self._callbacks[name] = []
            self._callbacks[name].append(on_failure)
    
    def unregister(self, name: str) -> None:
        """取消注册"""
        self._resources.pop(name, None)
        self._callbacks.pop(name, None)
    
    async def start(self) -> None:
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run())
    
    async def stop(self) -> None:
        """停止监控"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _run(self) -> None:
        """监控循环"""
        while self._running:
            await self._check_all()
            await asyncio.sleep(self._check_interval_ms / 1000)
    
    async def _check_all(self) -> None:
        """检查所有资源"""
        for name, resource in self._resources.items():
            check_fn = resource["check_fn"]
            
            try:
                if asyncio.iscoroutinefunction(check_fn):
                    is_healthy = await check_fn()
                else:
                    is_healthy = check_fn()
                
                resource["status"] = "healthy" if is_healthy else "unhealthy"
                resource["last_check"] = time.time()
                
                if not is_healthy:
                    resource["failure_count"] += 1
                    
                    # 调用失败回调
                    if name in self._callbacks:
                        for callback in self._callbacks[name]:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(name)
                                else:
                                    callback(name)
                            except Exception:
                                pass
                else:
                    resource["failure_count"] = 0
                    
            except Exception as e:
                resource["status"] = "error"
                resource["last_check"] = time.time()
                resource["failure_count"] += 1
    
    def get_status(self, name: str) -> Optional[dict]:
        """获取资源状态"""
        return self._resources.get(name)
    
    def get_all_status(self) -> dict:
        """获取所有状态"""
        return dict(self._resources)
    
    @property
    def is_running(self) -> bool:
        """是否运行中"""
        return self._running


class HealthCheck:
    """
    健康检查
    
    简单资源健康检查。
    """
    
    def __init__(self):
        self._checks: Dict[str, Callable] = {}
    
    def register(self, name: str, check_fn: Callable[[], bool]) -> None:
        """注册检查"""
        self._checks[name] = check_fn
    
    def check(self) -> dict:
        """执行检查"""
        results = {}
        
        for name, check_fn in self._checks.items():
            try:
                results[name] = {
                    "healthy": check_fn(),
                    "error": None,
                }
            except Exception as e:
                results[name] = {
                    "healthy": False,
                    "error": str(e),
                }
        
        return results
    
    @property
    def is_healthy(self) -> bool:
        """是否全部健康"""
        results = self.check()
        return all(r.get("healthy", False) for r in results.values())


# 导出
__all__ = [
    "AsyncWatcher",
    "HealthCheck",
]
