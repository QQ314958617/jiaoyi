"""
OpenClaw Cron Scheduler
====================
Inspired by Claude Code's src/utils/cron.ts.

Cron 表达式解析和调度器，支持：
1. Cron 表达式解析
2. 下次执行时间计算
3. 定时任务调度
4. 支持标准5字段格式
"""

from __future__ import annotations

import asyncio, croniter, time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Optional

# ============================================================================
# Cron 表达式
# ============================================================================

@dataclass
class CronExpression:
    """Cron 表达式"""
    expr: str  # "0 9 * * 1-5"  # minute hour day month weekday
    
    def __post_init__(self):
        self._cron = croniter.croniter(self.expr, datetime.now(timezone(timedelta(hours=8))))
    
    def next(self, base_time: Optional[datetime] = None) -> datetime:
        """获取下次执行时间"""
        if base_time:
            self._cron = croniter.croniter(self.expr, base_time)
        return self._cron.get_next(datetime)
    
    def prev(self, base_time: Optional[datetime] = None) -> datetime:
        """获取上次执行时间"""
        if base_time:
            self._cron = croniter.croniter(self.expr, base_time)
        return self._cron.get_prev(datetime)
    
    def get_next_run(self, after: Optional[datetime] = None) -> Optional[datetime]:
        """获取距离下次执行的时间差（秒）"""
        try:
            if after is None:
                after = datetime.now(timezone(timedelta(hours=8)))
            self._cron = croniter.croniter(self.expr, after)
            next_time = self._cron.get_next(datetime)
            return next_time
        except:
            return None
    
    @staticmethod
    def is_valid(expr: str) -> bool:
        """验证 cron 表达式"""
        try:
            croniter.croniter(expr)
            return True
        except:
            return False

# ============================================================================
# 常用 Cron 表达式
# ============================================================================

class CronPatterns:
    """常用 Cron 模式"""
    
    # 交易时间
    MARKET_OPEN = "0 9 * * 1-5"      # 周一到周五 9:00 开盘
    MARKET_CLOSE = "0 15 * * 1-5"    # 周一到周五 15:00 收盘
    MORNING_START = "0 9 * * 1-5"     # 早盘开始
    MORNING_END = "0 11 * * 1-5"      # 早盘结束（11:30）
    AFTERNOON_START = "0 13 * * 1-5"   # 午盘开始
    AFTERNOON_END = "0 15 * * 1-5"     # 午盘结束
    
    # 定时检查
    EVERY_5_MIN = "*/5 * * * *"      # 每5分钟
    EVERY_10_MIN = "*/10 * * * *"      # 每10分钟
    EVERY_15_MIN = "*/15 * * * *"      # 每15分钟
    EVERY_30_MIN = "*/30 * * * *"      # 每30分钟
    
    # 每天定时
    DAILY_0830 = "30 8 * * *"         # 每天 8:30
    DAILY_0900 = "0 9 * * *"          # 每天 9:00
    DAILY_2330 = "30 23 * * *"        # 每天 23:30
    DAILY_MIDNIGHT = "0 0 * * *"      # 每天午夜

# ============================================================================
# 定时任务
# ============================================================================

@dataclass
class ScheduledTask:
    """定时任务"""
    name: str
    func: Callable
    cron_expr: str
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0

class CronScheduler:
    """
    Cron 调度器
    
    用法：
    ```python
    scheduler = CronScheduler()
    
    def morning_routine():
        check_markets()
    
    scheduler.add("早盘检查", morning_routine, "0 9 * * 1-5")
    
    async def run():
        await scheduler.start()
    ```
    """
    
    def __init__(self, timezone_hours: int = 8):
        self._tasks: dict[str, ScheduledTask] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._tz = timezone(timedelta(hours=timezone_hours))
    
    def add(self, name: str, func: Callable, cron_expr: str, 
           enabled: bool = True) -> bool:
        """添加定时任务"""
        if not CronExpression.is_valid(cron_expr):
            return False
        
        self._tasks[name] = ScheduledTask(
            name=name,
            func=func,
            cron_expr=cron_expr,
            enabled=enabled
        )
        
        # 计算下次执行时间
        task = self._tasks[name]
        task.next_run = CronExpression(cron_expr).get_next_run()
        
        return True
    
    def remove(self, name: str) -> bool:
        """移除任务"""
        if name in self._tasks:
            del self._tasks[name]
            return True
        return False
    
    def enable(self, name: str) -> bool:
        """启用任务"""
        if name in self._tasks:
            self._tasks[name].enabled = True
            self._tasks[name].next_run = CronExpression(
                self._tasks[name].cron_expr
            ).get_next_run()
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用任务"""
        if name in self._tasks:
            self._tasks[name].enabled = False
            self._tasks[name].next_run = None
            return True
        return False
    
    def list_tasks(self) -> list[dict]:
        """列出所有任务"""
        result = []
        for task in self._tasks.values():
            result.append({
                "name": task.name,
                "cron": task.cron_expr,
                "enabled": task.enabled,
                "next_run": task.next_run.strftime("%Y-%m-%d %H:%M:%S") if task.next_run else None,
                "last_run": task.last_run.strftime("%Y-%m-%d %H:%M:%S") if task.last_run else None,
                "run_count": task.run_count,
                "error_count": task.error_count
            })
        return result
    
    async def start(self) -> None:
        """启动调度器"""
        self._running = True
        
        while self._running:
            now = datetime.now(self._tz)
            
            # 检查每个任务
            for name, task in list(self._tasks.items()):
                if not task.enabled or task.next_run is None:
                    continue
                
                # 检查是否应该执行
                if now >= task.next_run:
                    # 执行任务
                    try:
                        result = task.func()
                        
                        # 如果是协程，等待完成
                        if asyncio.iscoroutine(result):
                            await result
                        
                        task.last_run = now
                        task.run_count += 1
                        
                    except Exception as e:
                        task.error_count += 1
                        print(f"Task {name} error: {e}")
                    
                    # 计算下次执行时间
                    task.next_run = CronExpression(task.cron_expr).get_next_run(now)
            
            # 等待1秒
            await asyncio.sleep(1)
    
    def stop(self) -> None:
        """停止调度器"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None
    
    async def run_once(self) -> None:
        """立即执行所有任务（不等待）"""
        now = datetime.now(self._tz)
        
        for name, task in list(self._tasks.items()):
            if not task.enabled:
                continue
            
            try:
                result = task.func()
                if asyncio.iscoroutine(result):
                    await result
                
                task.last_run = now
                task.run_count += 1
                
            except Exception as e:
                task.error_count += 1
                print(f"Task {name} error: {e}")

# ============================================================================
# 便捷函数
# ============================================================================

def parse_cron(expr: str) -> Optional[CronExpression]:
    """解析 cron 表达式"""
    try:
        return CronExpression(expr)
    except:
        return None

def get_next_cron_run(expr: str, after: Optional[datetime] = None) -> Optional[datetime]:
    """获取下次执行时间"""
    cron = parse_cron(expr)
    if cron:
        return cron.get_next_run(after)
    return None

def format_next_run(expr: str, after: Optional[datetime] = None) -> str:
    """格式化下次执行时间"""
    next_run = get_next_cron_run(expr, after)
    if next_run:
        return next_run.strftime("%Y-%m-%d %H:%M:%S")
    return "无效的Cron表达式"
