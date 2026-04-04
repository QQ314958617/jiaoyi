"""
Metrics Collector - 指标收集器
基于 Claude Code metrics.ts 设计

收集和聚合指标数据。
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import threading


@dataclass
class Metric:
    """单个指标"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    指标收集器
    
    线程安全的指标收集和聚合。
    """
    
    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._metrics: List[Metric] = []
        self._lock = threading.Lock()
    
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """
        增加计数器
        
        Args:
            name: 指标名
            value: 增量
            tags: 标签
        """
        with self._lock:
            self._counters[name] += value
            self._record_metric(name, value, tags)
    
    def decrement(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """
        减少计数器
        
        Args:
            name: 指标名
            value: 减量
            tags: 标签
        """
        with self._lock:
            self._counters[name] -= value
            self._record_metric(name, -value, tags)
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        设置仪表值
        
        Args:
            name: 指标名
            value: 值
            tags: 标签
        """
        with self._lock:
            self._gauges[name] = value
            self._record_metric(name, value, tags)
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        记录直方图值
        
        Args:
            name: 指标名
            value: 值
            tags: 标签
        """
        with self._lock:
            self._histograms[name].append(value)
            self._record_metric(name, value, tags)
    
    def timing(self, name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        记录时间
        
        Args:
            name: 指标名
            duration_ms: 持续时间（毫秒）
            tags: 标签
        """
        self.histogram(f"{name}.timing", duration_ms, tags)
    
    def _record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]]) -> None:
        """记录原始指标"""
        self._metrics.append(Metric(
            name=name,
            value=value,
            timestamp=time.time(),
            tags=tags or {},
        ))
    
    def get_counter(self, name: str) -> float:
        """获取计数器值"""
        with self._lock:
            return self._counters.get(name, 0.0)
    
    def get_gauge(self, name: str) -> Optional[float]:
        """获取仪表值"""
        with self._lock:
            return self._gauges.get(name)
    
    def get_histogram_stats(self, name: str) -> Optional[Dict[str, float]]:
        """
        获取直方图统计
        
        Returns:
            {count, sum, min, max, avg, p50, p95, p99}
        """
        with self._lock:
            values = self._histograms.get(name, [])
            if not values:
                return None
            
            values_sorted = sorted(values)
            count = len(values_sorted)
            
            return {
                'count': count,
                'sum': sum(values_sorted),
                'min': values_sorted[0],
                'max': values_sorted[-1],
                'avg': sum(values_sorted) / count,
                'p50': values_sorted[int(count * 0.5)],
                'p95': values_sorted[int(count * 0.95)] if count >= 20 else values_sorted[-1],
                'p99': values_sorted[int(count * 0.99)] if count >= 100 else values_sorted[-1],
            }
    
    def get_all_metrics(self) -> Dict:
        """获取所有指标"""
        with self._lock:
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {
                    name: self._get_histogram_summary(values)
                    for name, values in self._histograms.items()
                },
            }
    
    def _get_histogram_summary(self, values: List[float]) -> Dict[str, float]:
        """获取直方图摘要"""
        if not values:
            return {}
        
        values_sorted = sorted(values)
        count = len(values_sorted)
        
        return {
            'count': count,
            'min': values_sorted[0],
            'max': values_sorted[-1],
            'avg': sum(values_sorted) / count,
        }
    
    def reset(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._metrics.clear()
    
    def get_recent_metrics(self, limit: int = 100) -> List[Metric]:
        """获取最近的指标"""
        with self._lock:
            return list(self._metrics[-limit:])


# 全局收集器
_global_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    return _global_collector


def increment(name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
    """全局增加计数器"""
    _global_collector.increment(name, value, tags)


def gauge(name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """全局设置仪表"""
    _global_collector.gauge(name, value, tags)


def histogram(name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """全局记录直方图"""
    _global_collector.histogram(name, value, tags)


def timing(name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None) -> None:
    """全局记录时间"""
    _global_collector.timing(name, duration_ms, tags)


# 导出
__all__ = [
    "Metric",
    "MetricsCollector",
    "get_metrics_collector",
    "increment",
    "gauge",
    "histogram",
    "timing",
]
