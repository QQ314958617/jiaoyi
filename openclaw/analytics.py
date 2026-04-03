"""
OpenClaw Analytics Service
=========================
Inspired by Claude Code's src/services/analytics/index.ts (173 lines).

交易系统专用事件分析服务，支持：
1. 事件队列（sink .attach 前的事件缓存）
2. 事件采样
3. 多后端（文件/Console/Sink）
4. Proto字段剥离（隐私保护）

Claude Code 设计亮点：
- attachAnalyticsSink(): 延迟初始化，队列在 sink 就绪后 drain
- stripProtoFields(): 剥离 _PROTO_* 敏感字段
- logEvent/logEventAsync: 同步/异步两种接口
- 事件采样：按配置的概率采样
"""

from __future__ import annotations

import json, time, threading, random, os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

# ============================================================================
# 类型定义
# ============================================================================

class EventSink:
    """事件后端接口"""
    def log_event(self, event_name: str, metadata: Dict[str, Any]) -> None:
        pass
    
    def log_event_async(self, event_name: str, metadata: Dict[str, Any]) -> None:
        pass

@dataclass
class QueuedEvent:
    event_name: str
    metadata: Dict[str, Any]
    is_async: bool = False

# ============================================================================
# 事件采样
# ============================================================================

class EventSampler:
    """事件采样器"""
    
    def __init__(self, sample_rate: float = 1.0, seed: Optional[int] = None):
        self.sample_rate = sample_rate
        self._random = random.Random(seed)
    
    def should_sample(self, event_name: str) -> bool:
        """判断是否应该采样这个事件"""
        return self._random.random() < self.sample_rate
    
    def sample_metadata(self, event_name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """添加采样元数据"""
        result = dict(metadata)
        if not self.should_sample(event_name):
            result["_sampled"] = False
        else:
            result["_sampled"] = True
            result["_sample_rate"] = self.sample_rate
        return result

# ============================================================================
# 分析服务
# ============================================================================

class AnalyticsService:
    """
    事件分析服务
    
    Claude Code 模式：
    - 事件队列：sink 未 attach 时缓存事件
    - attach 后 drain 队列
    - stripProtoFields: 剥离 _PROTO_* 字段
    - 采样：按概率采样事件
    
    交易系统用途：
    - 记录交易操作（买入/卖出）
    - 记录策略信号
    - 记录错误和异常
    - 记录性能指标
    """
    
    def __init__(self):
        self._sink: Optional[EventSink] = None
        self._queue: List[QueuedEvent] = []
        self._lock = threading.Lock()
        self._sampler = EventSampler(sample_rate=1.0)
        self._enabled = True
        self._event_counts: Dict[str, int] = {}
    
    def attach_sink(self, sink: EventSink) -> None:
        """
        附加事件后端
        
        如果队列中有事件，立即 drain
        """
        with self._lock:
            if self._sink is not None:
                return  # 已附加，幂等
            
            self._sink = sink
            
            if self._queue:
                events = list(self._queue)
                self._queue.clear()
                
                # 异步 drain，避免阻塞启动
                def drain():
                    for evt in events:
                        if evt.is_async:
                            try:
                                sink.log_event_async(evt.event_name, evt.metadata)
                            except Exception:
                                pass
                        else:
                            try:
                                sink.log_event(evt.event_name, evt.metadata)
                            except Exception:
                                pass
                
                # 使用 queueMicrotask 等效（在新线程中延迟执行）
                threading.Thread(target=drain, daemon=True).start()
    
    def log_event(self, event_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        记录事件（同步）
        
        如果 sink 未附加，事件入队
        """
        if not self._enabled:
            return
        
        metadata = metadata or {}
        
        # 采样
        metadata = self._sampler.sample_metadata(event_name, metadata)
        
        with self._lock:
            self._event_counts[event_name] = self._event_counts.get(event_name, 0) + 1
            
            if self._sink is None:
                self._queue.append(QueuedEvent(event_name, metadata, is_async=False))
                return
            
            try:
                self._sink.log_event(event_name, metadata)
            except Exception:
                pass
    
    def log_event_async(self, event_name: str, 
                        metadata: Optional[Dict[str, Any]] = None) -> None:
        """记录事件（异步）"""
        if not self._enabled:
            return
        
        metadata = metadata or {}
        metadata = self._sampler.sample_metadata(event_name, metadata)
        
        with self._lock:
            if self._sink is None:
                self._queue.append(QueuedEvent(event_name, metadata, is_async=True))
                return
        
        try:
            self._sink.log_event_async(event_name, metadata)
        except Exception:
            pass
    
    def strip_proto_fields(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        剥离 _PROTO_* 字段
        
        用于隐私保护，确保敏感字段不写入日志
        """
        result = None
        for key in list(metadata.keys()):
            if key.startswith("_PROTO_"):
                if result is None:
                    result = dict(metadata)
                del result[key]
        return result or metadata
    
    def set_sample_rate(self, rate: float) -> None:
        """设置采样率"""
        self._sampler = EventSampler(sample_rate=rate)
    
    def set_enabled(self, enabled: bool) -> None:
        """启用/禁用"""
        self._enabled = enabled
    
    def get_event_counts(self) -> Dict[str, int]:
        """获取事件计数"""
        with self._lock:
            return dict(self._event_counts)
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        with self._lock:
            return len(self._queue)
    
    def reset(self) -> None:
        """重置（仅用于测试）"""
        with self._lock:
            self._sink = None
            self._queue.clear()
            self._event_counts.clear()


# ============================================================================
# 内置 Sinks
# ============================================================================

class ConsoleSink(EventSink):
    """控制台输出 Sink"""
    
    def log_event(self, event_name: str, metadata: Dict[str, Any]) -> None:
        ts = datetime.now(timezone(timedelta(hours=8))).strftime("%H:%M:%S.%f")[:-3]
        print(f"[{ts}] 📊 {event_name} {json.dumps(metadata, ensure_ascii=False, default=str)}")
    
    def log_event_async(self, event_name: str, metadata: Dict[str, Any]) -> None:
        self.log_event(event_name, metadata)


class FileSink(EventSink):
    """文件输出 Sink（NDJSON格式）"""
    
    def __init__(self, log_dir: str = "/root/.openclaw/workspace/logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self._date = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
        self._path = os.path.join(log_dir, f"{self._date}.analytics.ndjson")
        self._lock = threading.Lock()
    
    def _ensure_today_file(self):
        """检查是否需要切换到新文件"""
        today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
        if today != self._date:
            self._date = today
            self._path = os.path.join(self._log_dir, f"{today}.analytics.ndjson")
    
    def log_event(self, event_name: str, metadata: Dict[str, Any]) -> None:
        self._ensure_today_file()
        ts = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = {"ts": ts, "event": event_name, **metadata}
        with self._lock:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    
    def log_event_async(self, event_name: str, metadata: Dict[str, Any]) -> None:
        self.log_event(event_name, metadata)


class CallbackSink(EventSink):
    """回调 Sink（用于自定义处理）"""
    
    def __init__(self, callback: Callable[[str, Dict[str, Any]], None]):
        self._callback = callback
    
    def log_event(self, event_name: str, metadata: Dict[str, Any]) -> None:
        try:
            self._callback(event_name, metadata)
        except Exception:
            pass
    
    def log_event_async(self, event_name: str, metadata: Dict[str, Any]) -> None:
        self.log_event(event_name, metadata)


# ============================================================================
# 全局实例
# ============================================================================

_analytics: Optional[AnalyticsService] = None
_analytics_lock = threading.Lock()

def get_analytics() -> AnalyticsService:
    """获取全局分析服务"""
    global _analytics
    with _analytics_lock:
        if _analytics is None:
            _analytics = AnalyticsService()
        return _analytics

def init_analytics(sink: Optional[EventSink] = None) -> AnalyticsService:
    """初始化分析服务"""
    analytics = get_analytics()
    if sink:
        analytics.attach_sink(sink)
    return analytics

# ============================================================================
# 便捷函数
# ============================================================================

def log_trade(action: str, stock_code: str, shares: int, price: float, 
              reason: str = "", result: str = "success") -> None:
    """记录交易事件"""
    get_analytics().log_event("trade", {
        "action": action,
        "stock_code": stock_code,
        "shares": shares,
        "price": price,
        "amount": shares * price,
        "reason": reason,
        "result": result,
    })

def log_signal(strategy: str, stock_code: str, signal: str, 
               strength: float = 1.0) -> None:
    """记录策略信号"""
    get_analytics().log_event("signal", {
        "strategy": strategy,
        "stock_code": stock_code,
        "signal": signal,
        "strength": strength,
    })

def log_error(error_type: str, message: str, details: Optional[Dict] = None) -> None:
    """记录错误"""
    get_analytics().log_event("error", {
        "type": error_type,
        "message": message,
        "details": details or {},
    })
