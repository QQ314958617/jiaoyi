"""
Trace - 追踪
基于 Claude Code trace.ts 设计

调用追踪工具。
"""
import time
from typing import Any, Callable, Dict, List, Optional
from contextvars import ContextVar


# 上下文变量存储追踪ID
_current_trace: ContextVar[Optional[str]] = ContextVar('current_trace', default=None)
_current_span: ContextVar[Optional[str]] = ContextVar('current_span', default=None)


class Span:
    """
    追踪跨度
    
    代表一个操作单元。
    """
    
    def __init__(
        self,
        name: str,
        trace_id: str,
        parent_id: Optional[str] = None,
    ):
        self.name = name
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.span_id = f"{trace_id}.{time.time_ns()}"
        
        self._start_time = time.time()
        self._end_time: Optional[float] = None
        self._tags: Dict[str, Any] = {}
        self._logs: List[dict] = []
    
    def end(self) -> None:
        """结束跨度"""
        self._end_time = time.time()
    
    @property
    def duration_ms(self) -> float:
        """持续时间（毫秒）"""
        if self._end_time is None:
            return (time.time() - self._start_time) * 1000
        return (self._end_time - self._start_time) * 1000
    
    def tag(self, key: str, value: Any) -> "Span":
        """添加标签"""
        self._tags[key] = value
        return self
    
    def log(self, message: str, **attrs) -> "Span":
        """添加日志"""
        self._logs.append({
            "message": message,
            "timestamp": time.time(),
            **attrs,
        })
        return self
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "span_id": self.span_id,
            "start_time": self._start_time,
            "end_time": self._end_time,
            "duration_ms": self.duration_ms,
            "tags": self._tags,
            "logs": self._logs,
        }


class Tracer:
    """
    追踪器
    
    创建和管理追踪跨度。
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._spans: List[Span] = []
    
    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Span:
        """开始新跨度"""
        if trace_id is None:
            trace_id = _current_trace.get() or self._generate_trace_id()
        
        if parent_id is None:
            parent_id = _current_span.get()
        
        span = Span(name, trace_id, parent_id)
        _current_span.set(span.span_id)
        self._spans.append(span)
        
        return span
    
    def end_span(self, span: Span) -> None:
        """结束跨度"""
        span.end()
        _current_span.set(span.parent_id)
    
    def _generate_trace_id(self) -> str:
        """生成追踪ID"""
        return f"{self.service_name}.{time.time_ns()}"
    
    def get_spans(self) -> List[dict]:
        """获取所有跨度"""
        return [s.to_dict() for s in self._spans]
    
    def clear(self) -> None:
        """清空"""
        self._spans.clear()


def traced(
    tracer: Tracer,
    span_name: Optional[str] = None,
):
    """
    追踪装饰器
    
    Args:
        tracer: 追踪器
        span_name: 跨度名称（默认使用函数名）
    """
    def decorator(func: Callable) -> Callable:
        name = span_name or func.__name__
        
        def sync_wrapper(*args, **kwargs):
            span = tracer.start_span(name)
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                span.tag("error", True)
                span.log(str(e))
                raise
            finally:
                tracer.end_span(span)
        
        async def async_wrapper(*args, **kwargs):
            span = tracer.start_span(name)
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                span.tag("error", True)
                span.log(str(e))
                raise
            finally:
                tracer.end_span(span)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper


# 全局追踪器
_global_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "default") -> Tracer:
    """获取全局追踪器"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer(service_name)
    return _global_tracer


# 导出
__all__ = [
    "Span",
    "Tracer",
    "traced",
    "get_tracer",
    "current_trace",
    "current_span",
]

# 别名导出
current_trace = _current_trace
current_span = _current_span
