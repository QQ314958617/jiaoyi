"""
Metric - 指标
基于 Claude Code metric.ts 设计

指标收集工具。
"""
import time
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict
from threading import Lock


class Counter:
    """
    计数器指标
    
    累加值。
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0
        self._lock = Lock()
    
    def increment(self, delta: float = 1) -> None:
        """递增"""
        with self._lock:
            self._value += delta
    
    def decrement(self, delta: float = 1) -> None:
        """递减"""
        with self._lock:
            self._value -= delta
    
    def get(self) -> float:
        """获取当前值"""
        with self._lock:
            return self._value
    
    def reset(self) -> None:
        """重置"""
        with self._lock:
            self._value = 0


class Gauge:
    """
    仪表指标
    
    当前值。
    """
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._value = 0.0
        self._lock = Lock()
    
    def set(self, value: float) -> None:
        """设置值"""
        with self._lock:
            self._value = value
    
    def get(self) -> float:
        """获取值"""
        with self._lock:
            return self._value
    
    def increment(self, delta: float = 1) -> None:
        """递增"""
        with self._lock:
            self._value += delta
    
    def decrement(self, delta: float = 1) -> None:
        """递减"""
        with self._lock:
            self._value -= delta


class Histogram:
    """
    直方图指标
    
    统计分布。
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        buckets: List[float] = None,
    ):
        self.name = name
        self.description = description
        self._buckets = buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
        self._values: List[float] = []
        self._sum = 0.0
        self._count = 0
        self._lock = Lock()
    
    def observe(self, value: float) -> None:
        """记录观测值"""
        with self._lock:
            self._values.append(value)
            self._sum += value
            self._count += 1
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        with self._lock:
            if not self._values:
                return {
                    "count": 0,
                    "sum": 0,
                    "min": 0,
                    "max": 0,
                    "mean": 0,
                    "p50": 0,
                    "p90": 0,
                    "p99": 0,
                }
            
            sorted_values = sorted(self._values)
            count = len(sorted_values)
            
            def percentile(p: float) -> float:
                idx = int(count * p)
                return sorted_values[min(idx, count - 1)]
            
            return {
                "count": self._count,
                "sum": self._sum,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "mean": self._sum / count,
                "p50": percentile(0.5),
                "p90": percentile(0.9),
                "p99": percentile(0.99),
            }


class Timer:
    """
    计时器指标
    
    测量持续时间。
    """
    
    def __init__(self, histogram: Histogram):
        self._histogram = histogram
        self._start_time: Optional[float] = None
    
    def start(self) -> "Timer":
        """开始计时"""
        self._start_time = time.time()
        return self
    
    def stop(self) -> float:
        """停止计时并记录"""
        if self._start_time is None:
            raise RuntimeError("Timer not started")
        
        duration = time.time() - self._start_time
        self._histogram.observe(duration)
        self._start_time = None
        return duration
    
    def __enter__(self) -> "Timer":
        self.start()
        return self
    
    def __exit__(self, *args) -> None:
        self.stop()
    
    async def __aenter__(self) -> "Timer":
        self.start()
        return self
    
    async def __aexit__(self, *args) -> None:
        self.stop()


class Metrics:
    """
    指标收集器
    
    管理所有指标。
    """
    
    def __init__(self):
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._lock = Lock()
    
    def counter(self, name: str, description: str = "") -> Counter:
        """获取或创建计数器"""
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, description)
            return self._counters[name]
    
    def gauge(self, name: str, description: str = "") -> Gauge:
        """获取或创建仪表"""
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, description)
            return self._gauges[name]
    
    def histogram(self, name: str, description: str = "") -> Histogram:
        """获取或创建直方图"""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, description)
            return self._histograms[name]
    
    def timer(self, name: str) -> Timer:
        """获取计时器"""
        return Timer(self.histogram(name))
    
    def get_all(self) -> dict:
        """获取所有指标"""
        with self._lock:
            return {
                "counters": {k: v.get() for k, v in self._counters.items()},
                "gauges": {k: v.get() for k, v in self._gauges.items()},
                "histograms": {k: v.get_stats() for k, v in self._histograms.items()},
            }


# 全局指标收集器
_global_metrics = Metrics()


def metrics() -> Metrics:
    """获取全局指标收集器"""
    return _global_metrics


# 导出
__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "Timer",
    "Metrics",
    "metrics",
]
