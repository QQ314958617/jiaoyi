"""
Perfetto Tracing for OpenClaw

Generates traces in the Chrome Trace Event format viewable at ui.perfetto.dev.
Outputs JSON with traceEvents array following Chrome Trace Event format spec:
https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU

Env vars:
  OPENCLAW_PERFETTO_TRACE=1 or =<path>   Enable tracing
  OPENCLAW_PERFETTO_WRITE_INTERVAL_S=N   Periodic write interval (seconds)

Usage:
  from openclaw.perfetto_tracing import initialize_tracing, is_tracing_enabled

  initialize_tracing()
  if is_tracing_enabled():
      span_id = start_llm_span(model="...", prompt_tokens=...)
      # ... do work ...
      end_llm_span(span_id, ttft_ms=..., ttlt_ms=...)
"""

from __future__ import annotations

import asyncio
import atexit
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# Trace Event types (Chrome Trace Event format)
# https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU
# ---------------------------------------------------------------------------

class TracePhase(str, Enum):
    """Chrome Trace Event phase values."""
    BEGIN = "B"           # Begin duration event
    END = "E"             # End duration event
    COMPLETE = "X"        # Complete event with duration
    INSTANT = "i"         # Instant event
    COUNTER = "C"         # Counter event
    ASYNC_BEGIN = "b"     # Async begin
    ASYNC_INSTANT = "n"   # Async instant
    ASYNC_END = "e"       # Async end
    METADATA = "M"        # Metadata event


@dataclass
class TraceEvent:
    """
    Single trace event in Chrome Trace Event format.

    Required fields: name, cat, ph, ts, pid, tid
    Optional: dur, args, id, scope
    """
    name: str
    cat: str
    ph: str  # TracePhase value
    ts: int       # Timestamp in microseconds (μs) relative to trace start
    pid: int      # Process ID (1=main, agent IDs for subagents)
    tid: int      # Thread ID (numeric hash of agent name or 1 for main)
    dur: Optional[int] = None   # Duration in microseconds (for COMPLETE events)
    args: Optional[dict[str, Any]] = None
    id: Optional[str] = None    # For async events
    scope: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        ph_val = self.ph.value if isinstance(self.ph, TracePhase) else self.ph
        result = {
            "name": self.name,
            "cat": self.cat,
            "ph": ph_val,
            "ts": self.ts,
            "pid": self.pid,
            "tid": self.tid,
        }
        if self.dur is not None:
            result["dur"] = self.dur
        if self.args:
            result["args"] = self.args
        if self.id is not None:
            result["id"] = self.id
        if self.scope is not None:
            result["scope"] = self.scope
        return result


@dataclass
class AgentInfo:
    """Agent tracking info for trace hierarchy."""
    agent_id: str
    agent_name: str
    parent_agent_id: Optional[str] = None
    process_id: int = 1
    thread_id: int = 1


@dataclass
class PendingSpan:
    """Tracks an in-flight span (begin emitted, end not yet emitted)."""
    name: str
    category: str
    start_ts: int       # microseconds relative to trace start
    agent_info: AgentInfo
    args: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

_is_enabled = False
_trace_path: Optional[str] = None
_start_time_ms: int = 0
_trace_written = False

# Event storage — metadata events survive eviction, regular events are capped
_metadata_events: list[TraceEvent] = []
_events: list[TraceEvent] = []
MAX_EVENTS = 100_000

# Pending spans (begin emitted, end not yet)
_pending_spans: dict[str, PendingSpan] = {}

# Agent registry
_agent_registry: dict[str, AgentInfo] = {}
_process_id_counter = 1
_agent_id_to_process_id: dict[str, int] = {}

# Span ID counter
_span_id_counter = 0

# Periodic write
_write_interval_s: Optional[float] = None
_write_timer: Optional[threading.Timer] = None

# Stale span cleanup
STALE_SPAN_TTL_MS = 30 * 60 * 1000   # 30 minutes
STALE_CLEANUP_INTERVAL_MS = 60 * 1000  # 1 minute
_stale_cleanup_timer: Optional[threading.Timer] = None

# Lock for thread safety
_lock = threading.RLock()

# Callbacks for getting agent context (set by openclaw core)
_get_agent_id_func: Optional[Callable[[], Optional[str]]] = None
_get_agent_name_func: Optional[Callable[[], Optional[str]]] = None
_get_session_id_func: Optional[Callable[[], Optional[str]]] = None
_get_parent_session_id_func: Optional[Callable[[], Optional[str]]] = None
_get_config_home_func: Optional[Callable[[], str]] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _djb2_hash(s: str) -> int:
    """djb2 hash — must match the JS implementation."""
    h = 5381
    for c in s:
        h = (h * 33) ^ ord(c)
    return abs(h)


def _string_to_numeric_hash(s: str) -> int:
    """Convert string to numeric hash for use as thread ID."""
    return _djb2_hash(s) or 1


def _get_process_id_for_agent(agent_id: str) -> int:
    """Map agent ID to a numeric process ID (Perfetto requires numeric)."""
    global _process_id_counter
    with _lock:
        if agent_id in _agent_id_to_process_id:
            return _agent_id_to_process_id[agent_id]
        _process_id_counter += 1
        new_pid = _process_id_counter
        _agent_id_to_process_id[agent_id] = new_pid
        return new_pid


def _get_timestamp() -> int:
    """Microseconds since trace start."""
    return (int(time.time() * 1_000_000) - _start_time_ms)


def _generate_span_id() -> str:
    global _span_id_counter
    with _lock:
        _span_id_counter += 1
        return f"span_{_span_id_counter}"


def _get_session_id() -> str:
    global _get_session_id_func
    if _get_session_id_func:
        return _get_session_id_func() or "unknown"
    return os.environ.get("OPENCLAW_SESSION_ID", "unknown")


def _get_agent_id() -> Optional[str]:
    global _get_agent_id_func
    if _get_agent_id_func:
        return _get_agent_id_func()
    return None


def _get_agent_name() -> str:
    global _get_agent_name_func
    if _get_agent_name_func:
        return _get_agent_name_func() or "main"
    return "main"


def _get_parent_session_id() -> Optional[str]:
    global _get_parent_session_id_func
    if _get_parent_session_id_func:
        return _get_parent_session_id_func()
    return None


def _resolve_config_home() -> str:
    global _get_config_home_func
    if _get_config_home_func:
        return _get_config_home_func()
    return os.path.expanduser("~/.config")


# ---------------------------------------------------------------------------
# Agent info helpers
# ---------------------------------------------------------------------------

def _get_current_agent_info() -> AgentInfo:
    """Get or create AgentInfo for the current agent."""
    agent_id = _get_agent_id() or _get_session_id()
    agent_name = _get_agent_name()

    with _lock:
        if agent_id in _agent_registry:
            return _agent_registry[agent_id]

        session_id = _get_session_id()
        info = AgentInfo(
            agent_id=agent_id,
            agent_name=agent_name,
            parent_agent_id=_get_parent_session_id(),
            process_id=1 if agent_id == session_id else _get_process_id_for_agent(agent_id),
            thread_id=_string_to_numeric_hash(agent_name),
        )
        _agent_registry[agent_id] = info
        return info


# ---------------------------------------------------------------------------
# Trace building
# ---------------------------------------------------------------------------

def _build_trace_document() -> str:
    """Build the full trace JSON document."""
    import json
    # Use default=str to handle any non-serializable values
    return json.dumps({
        "traceEvents": [_e.to_dict() for _e in (*_metadata_events, *_events)],
        "metadata": {
            "session_id": _get_session_id(),
            "trace_start_time": datetime.fromtimestamp(
                _start_time_ms / 1_000_000, tz=timezone.utc
            ).isoformat(),
            "agent_count": len(_agent_registry),
            "total_event_count": len(_metadata_events) + len(_events),
        }
    }, default=str)


# ---------------------------------------------------------------------------
# Event eviction
# ---------------------------------------------------------------------------

def _evict_stale_spans() -> None:
    """Evict pending spans older than STALE_SPAN_TTL_MS."""
    now = _get_timestamp()
    ttl_us = STALE_SPAN_TTL_MS * 1000  # ms → μs

    with _lock:
        stale_ids = [
            sid for sid, span in _pending_spans.items()
            if now - span.start_ts > ttl_us
        ]

    for sid in stale_ids:
        span = _pending_spans.pop(sid, None)
        if span:
            _events.append(TraceEvent(
                name=span.name,
                cat=span.category,
                ph=TracePhase.END,
                ts=now,
                pid=span.agent_info.process_id,
                tid=span.agent_info.thread_id,
                args={**span.args, "evicted": True,
                       "duration_ms": (now - span.start_ts) / 1000},
            ))


def _evict_oldest_events() -> None:
    """Drop the oldest half of events when MAX_EVENTS is exceeded.

    Inserts a trace_truncated marker so the gap is visible in Perfetto UI.
    """
    global _events
    with _lock:
        if len(_events) < MAX_EVENTS:
            return

        dropped_count = MAX_EVENTS // 2
        dropped = _events[:dropped_count]
        _events = _events[dropped_count:]

        # Insert synthetic truncation marker
        marker_ts = dropped[-1].ts if dropped else 0
        _events.insert(0, TraceEvent(
            name="trace_truncated",
            cat="__metadata",
            ph=TracePhase.INSTANT,
            ts=marker_ts,
            pid=1,
            tid=0,
            args={"dropped_events": dropped_count},
        ))


def _periodic_cleanup() -> None:
    """Called every STALE_CLEANUP_INTERVAL_MS to evict stale data."""
    _evict_stale_spans()
    _evict_oldest_events()


# ---------------------------------------------------------------------------
# Periodic write
# ---------------------------------------------------------------------------

def _stop_write_timer() -> None:
    global _write_timer, _stale_cleanup_timer
    if _write_timer:
        _write_timer.cancel()
        _write_timer = None
    if _stale_cleanup_timer:
        _stale_cleanup_timer.cancel()
        _stale_cleanup_timer = None


async def _async_write_trace(path: str) -> None:
    """Async helper to write trace file."""
    import json
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(_sync_write_trace, path)


def _sync_write_trace(path: str) -> None:
    """Synchronous trace write."""
    import json
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_build_trace_document())


def _do_periodic_write() -> None:
    """Periodic write callback."""
    global _trace_written
    if not _is_enabled or not _trace_path or _trace_written:
        return
    try:
        _sync_write_trace(_trace_path)
    except Exception:
        pass  # Swallow errors — next tick will retry


def _schedule_next_write() -> None:
    """Reschedule the periodic write timer."""
    global _write_timer, _write_interval_s
    _stop_write_timer()
    if _write_interval_s and _write_interval_s > 0:
        _write_timer = threading.Timer(
            _write_interval_s,
            _run_write_and_reschedule
        )
        _write_timer.daemon = True
        _write_timer.start()


def _run_write_and_reschedule() -> None:
    _do_periodic_write()
    _schedule_next_write()


async def _async_final_write() -> None:
    """Final async write on shutdown."""
    global _trace_written
    if not _is_enabled or not _trace_path or _trace_written:
        return
    _stop_write_timer()
    _close_open_spans()
    try:
        await _async_write_trace(_trace_path)
        _trace_written = True
    except Exception:
        pass


def _final_sync_write() -> None:
    """Synchronous final write (called from atexit)."""
    global _trace_written
    if not _is_enabled or not _trace_path or _trace_written:
        return
    _stop_write_timer()
    _close_open_spans()
    try:
        _sync_write_trace(_trace_path)
        _trace_written = True
    except Exception:
        pass


def _close_open_spans() -> None:
    """Force-close any remaining open spans at session end."""
    now = _get_timestamp()
    with _lock:
        span_ids = list(_pending_spans.keys())
    for sid in span_ids:
        span = _pending_spans.pop(sid, None)
        if span:
            _events.append(TraceEvent(
                name=span.name,
                cat=span.category,
                ph=TracePhase.END,
                ts=now,
                pid=span.agent_info.process_id,
                tid=span.agent_info.thread_id,
                args={
                    **span.args,
                    "incomplete": True,
                    "duration_ms": (now - span.start_ts) / 1000,
                },
            ))


def _emit_process_metadata(agent_info: AgentInfo) -> None:
    """Emit __metadata events (process_name, thread_name, parent_agent)."""
    if not _is_enabled:
        return
    _metadata_events.append(TraceEvent(
        name="process_name",
        cat="__metadata",
        ph=TracePhase.METADATA,
        ts=0,
        pid=agent_info.process_id,
        tid=0,
        args={"name": agent_info.agent_name},
    ))
    _metadata_events.append(TraceEvent(
        name="thread_name",
        cat="__metadata",
        ph=TracePhase.METADATA,
        ts=0,
        pid=agent_info.process_id,
        tid=agent_info.thread_id,
        args={"name": agent_info.agent_name},
    ))
    if agent_info.parent_agent_id:
        _metadata_events.append(TraceEvent(
            name="parent_agent",
            cat="__metadata",
            ph=TracePhase.METADATA,
            ts=0,
            pid=agent_info.process_id,
            tid=0,
            args={"parent_agent_id": agent_info.parent_agent_id},
        ))


# ---------------------------------------------------------------------------
# Public API: initialization
# ---------------------------------------------------------------------------

def initialize_tracing(
    get_agent_id_fn: Optional[Callable[[], Optional[str]]] = None,
    get_agent_name_fn: Optional[Callable[[], Optional[str]]] = None,
    get_session_id_fn: Optional[Callable[[], Optional[str]]] = None,
    get_parent_session_id_fn: Optional[Callable[[], Optional[str]]] = None,
    get_config_home_fn: Optional[Callable[[], str]] = None,
) -> None:
    """
    Initialize Perfetto tracing.

    Call this early in the application lifecycle. Only effective when
    OPENCLAW_PERFETTO_TRACE=1 or OPENCLAW_PERFETTO_TRACE=<path> is set.

    Context callbacks allow injecting OpenClaw's runtime identity:
      get_agent_id_fn()       -> current agent ID
      get_agent_name_fn()     -> current agent name
      get_session_id_fn()     -> session ID
      get_parent_session_id_fn() -> parent session ID
      get_config_home_fn()    -> config directory path
    """
    global _is_enabled, _trace_path, _start_time_ms
    global _write_interval_s, _write_timer, _stale_cleanup_timer
    global _get_agent_id_func, _get_agent_name_func
    global _get_session_id_func, _get_parent_session_id_func
    global _get_config_home_func

    # Wire up context callbacks
    if get_agent_id_fn is not None:
        _get_agent_id_func = get_agent_id_fn
    if get_agent_name_fn is not None:
        _get_agent_name_func = get_agent_name_fn
    if get_session_id_fn is not None:
        _get_session_id_func = get_session_id_fn
    if get_parent_session_id_fn is not None:
        _get_parent_session_id_func = get_parent_session_id_fn
    if get_config_home_fn is not None:
        _get_config_home_func = get_config_home_fn

    env_value = os.environ.get("OPENCLAW_PERFETTO_TRACE", "")
    if not env_value or env_value.lower() in ("0", "false", "no", "off"):
        return

    _is_enabled = True
    _start_time_ms = int(time.time() * 1_000_000)  # μs

    if env_value in ("1", "true", "yes", "on"):
        traces_dir = Path(_resolve_config_home()) / "traces"
        _trace_path = str(traces_dir / f"trace-{_get_session_id()}.json")
    else:
        _trace_path = env_value

    # Periodic write interval
    interval_s = os.environ.get("OPENCLAW_PERFETTO_WRITE_INTERVAL_S", "")
    try:
        _write_interval_s = float(interval_s) if interval_s else None
    except ValueError:
        _write_interval_s = None

    if _write_interval_s and _write_interval_s > 0:
        _schedule_next_write()

    # Stale span cleanup timer
    _stale_cleanup_timer = threading.Timer(
        STALE_CLEANUP_INTERVAL_MS / 1000,
        _run_periodic_cleanup_and_reschedule
    )
    _stale_cleanup_timer.daemon = True
    _stale_cleanup_timer.start()

    # Register atexit fallback
    atexit.register(_final_sync_write)

    # Emit main process metadata
    agent_info = _get_current_agent_info()
    _emit_process_metadata(agent_info)


def _run_periodic_cleanup_and_reschedule() -> None:
    _periodic_cleanup()
    global _stale_cleanup_timer
    _stale_cleanup_timer = threading.Timer(
        STALE_CLEANUP_INTERVAL_MS / 1000,
        _run_periodic_cleanup_and_reschedule
    )
    _stale_cleanup_timer.daemon = True
    _stale_cleanup_timer.start()


def is_tracing_enabled() -> bool:
    """Return True if Perfetto tracing is active."""
    return _is_enabled


# ---------------------------------------------------------------------------
# Public API: span lifecycle
# ---------------------------------------------------------------------------

def start_llm_span(
    model: str,
    prompt_tokens: Optional[int] = None,
    message_id: Optional[str] = None,
    is_speculative: bool = False,
    query_source: Optional[str] = None,
) -> str:
    """
    Start an LLM/API call span.

    Returns a span_id to pass to end_llm_span().
    """
    if not _is_enabled:
        return ""

    span_id = _generate_span_id()
    agent_info = _get_current_agent_info()
    now = _get_timestamp()

    pending = PendingSpan(
        name="API Call",
        category="api",
        start_ts=now,
        agent_info=agent_info,
        args={
            "model": model,
            "prompt_tokens": prompt_tokens,
            "message_id": message_id,
            "is_speculative": is_speculative,
            "query_source": query_source,
        },
    )
    _pending_spans[span_id] = pending

    _events.append(TraceEvent(
        name="API Call",
        cat="api",
        ph=TracePhase.BEGIN,
        ts=now,
        pid=agent_info.process_id,
        tid=agent_info.thread_id,
        args=pending.args,
    ))
    return span_id


def end_llm_span(
    span_id: str,
    ttft_ms: Optional[float] = None,
    ttlt_ms: Optional[float] = None,
    prompt_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    cache_read_tokens: Optional[int] = None,
    cache_creation_tokens: Optional[int] = None,
    message_id: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None,
    request_setup_ms: Optional[float] = None,
    attempt_start_times: Optional[list[float]] = None,
) -> None:
    """
    End an LLM/API call span with response metadata.

    Derived metrics computed automatically:
      - itps: input tokens per second (prompt processing speed)
      - otps: output tokens per second (sampling speed)
      - cache_hit_rate_pct: percentage of prompt tokens served from cache
    """
    if not _is_enabled or not span_id:
        return

    pending = _pending_spans.pop(span_id, None)
    if not pending:
        return

    now = _get_timestamp()
    duration_us = now - pending.start_ts

    prompt_tokens = prompt_tokens or pending.args.get("prompt_tokens")
    output_tokens = output_tokens
    cache_read_tokens = cache_read_tokens

    # Compute derived metrics
    itps = None
    otps = None
    cache_hit_rate_pct = None

    if ttft_ms is not None and prompt_tokens is not None and ttft_ms > 0:
        itps = round((prompt_tokens / (ttft_ms / 1000)) * 100) / 100

    sampling_ms = None
    if ttlt_ms is not None and ttft_ms is not None:
        sampling_ms = ttlt_ms - ttft_ms

    if sampling_ms is not None and output_tokens is not None and sampling_ms > 0:
        otps = round((output_tokens / (sampling_ms / 1000)) * 100) / 100

    if cache_read_tokens is not None and prompt_tokens and prompt_tokens > 0:
        cache_hit_rate_pct = round((cache_read_tokens / prompt_tokens) * 10000) / 100

    setup_us = (request_setup_ms * 1000) if request_setup_ms and request_setup_ms > 0 else 0

    args = {
        **pending.args,
        "ttft_ms": ttft_ms,
        "ttlt_ms": ttlt_ms,
        "prompt_tokens": prompt_tokens,
        "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_creation_tokens": cache_creation_tokens,
        "message_id": message_id or pending.args.get("message_id"),
        "success": success,
        "error": error,
        "duration_ms": duration_us / 1000,
        "request_setup_ms": request_setup_ms,
        "itps": itps,
        "otps": otps,
        "cache_hit_rate_pct": cache_hit_rate_pct,
    }

    # Emit Request Setup sub-span
    if setup_us > 0:
        setup_end_ts = pending.start_ts + setup_us
        _events.append(TraceEvent(
            name="Request Setup",
            cat="api,setup",
            ph=TracePhase.BEGIN,
            ts=pending.start_ts,
            pid=pending.agent_info.process_id,
            tid=pending.agent_info.thread_id,
            args={
                "request_setup_ms": request_setup_ms,
                "attempt_count": len(attempt_start_times) if attempt_start_times else 1,
            },
        ))

        # Retry sub-spans
        if attempt_start_times and len(attempt_start_times) > 1:
            base_wall_ms = attempt_start_times[0]
            for i in range(len(attempt_start_times) - 1):
                attempt_start_us = pending.start_ts + (attempt_start_times[i] - base_wall_ms) * 1000
                attempt_end_us = pending.start_ts + (attempt_start_times[i + 1] - base_wall_ms) * 1000
                for ph, ts in [(TracePhase.BEGIN, attempt_start_us), (TracePhase.END, attempt_end_us)]:
                    _events.append(TraceEvent(
                        name=f"Attempt {i + 1} (retry)",
                        cat="api,retry",
                        ph=ph,
                        ts=ts,
                        pid=pending.agent_info.process_id,
                        tid=pending.agent_info.thread_id,
                    ))

        _events.append(TraceEvent(
            name="Request Setup",
            cat="api,setup",
            ph=TracePhase.END,
            ts=setup_end_ts,
            pid=pending.agent_info.process_id,
            tid=pending.agent_info.thread_id,
        ))

    # First Token and Sampling sub-spans
    if ttft_ms is not None:
        first_token_start_ts = pending.start_ts + setup_us
        first_token_end_ts = first_token_start_ts + int(ttft_ms * 1000)

        _events.append(TraceEvent(
            name="First Token",
            cat="api,ttft",
            ph=TracePhase.BEGIN,
            ts=first_token_start_ts,
            pid=pending.agent_info.process_id,
            tid=pending.agent_info.thread_id,
            args={
                "ttft_ms": ttft_ms,
                "prompt_tokens": prompt_tokens,
                "itps": itps,
                "cache_hit_rate_pct": cache_hit_rate_pct,
            },
        ))
        _events.append(TraceEvent(
            name="First Token",
            cat="api,ttft",
            ph=TracePhase.END,
            ts=first_token_end_ts,
            pid=pending.agent_info.process_id,
            tid=pending.agent_info.thread_id,
        ))

        # Sampling phase
        actual_sampling_ms = None
        if ttlt_ms is not None and ttft_ms is not None:
            setup = request_setup_ms or 0
            actual_sampling_ms = ttlt_ms - ttft_ms - setup
        if actual_sampling_ms and actual_sampling_ms > 0:
            sampling_end_ts = first_token_end_ts + int(actual_sampling_ms * 1000)
            _events.append(TraceEvent(
                name="Sampling",
                cat="api,sampling",
                ph=TracePhase.BEGIN,
                ts=first_token_end_ts,
                pid=pending.agent_info.process_id,
                tid=pending.agent_info.thread_id,
                args={
                    "sampling_ms": actual_sampling_ms,
                    "output_tokens": output_tokens,
                    "otps": otps,
                },
            ))
            _events.append(TraceEvent(
                name="Sampling",
                cat="api,sampling",
                ph=TracePhase.END,
                ts=sampling_end_ts,
                pid=pending.agent_info.process_id,
                tid=pending.agent_info.thread_id,
            ))

    # End event
    _events.append(TraceEvent(
        name=pending.name,
        cat=pending.category,
        ph=TracePhase.END,
        ts=now,
        pid=pending.agent_info.process_id,
        tid=pending.agent_info.thread_id,
        args=args,
    ))


def start_tool_span(
    tool_name: str,
    **kwargs: Any,
) -> str:
    """Start a tool execution span. Returns span_id."""
    if not _is_enabled:
        return ""

    span_id = _generate_span_id()
    agent_info = _get_current_agent_info()
    now = _get_timestamp()

    pending = PendingSpan(
        name=f"Tool: {tool_name}",
        category="tool",
        start_ts=now,
        agent_info=agent_info,
        args={"tool_name": tool_name, **kwargs},
    )
    _pending_spans[span_id] = pending

    _events.append(TraceEvent(
        name=f"Tool: {tool_name}",
        cat="tool",
        ph=TracePhase.BEGIN,
        ts=now,
        pid=agent_info.process_id,
        tid=agent_info.thread_id,
        args=pending.args,
    ))
    return span_id


def end_tool_span(
    span_id: str,
    success: bool = True,
    error: Optional[str] = None,
    result_tokens: Optional[int] = None,
) -> None:
    """End a tool execution span."""
    if not _is_enabled or not span_id:
        return

    pending = _pending_spans.pop(span_id, None)
    if not pending:
        return

    now = _get_timestamp()
    duration_us = now - pending.start_ts

    _events.append(TraceEvent(
        name=pending.name,
        cat=pending.category,
        ph=TracePhase.END,
        ts=now,
        pid=pending.agent_info.process_id,
        tid=pending.agent_info.thread_id,
        args={
            **pending.args,
            "success": success,
            "error": error,
            "result_tokens": result_tokens,
            "duration_ms": duration_us / 1000,
        },
    ))


def start_user_input_span(context: Optional[str] = None) -> str:
    """Start a user input waiting span."""
    if not _is_enabled:
        return ""

    span_id = _generate_span_id()
    agent_info = _get_current_agent_info()
    now = _get_timestamp()

    pending = PendingSpan(
        name="Waiting for User Input",
        category="user_input",
        start_ts=now,
        agent_info=agent_info,
        args={"context": context},
    )
    _pending_spans[span_id] = pending

    _events.append(TraceEvent(
        name="Waiting for User Input",
        cat="user_input",
        ph=TracePhase.BEGIN,
        ts=now,
        pid=agent_info.process_id,
        tid=agent_info.thread_id,
        args=pending.args,
    ))
    return span_id


def end_user_input_span(
    span_id: str,
    decision: Optional[str] = None,
    source: Optional[str] = None,
) -> None:
    """End a user input waiting span."""
    if not _is_enabled or not span_id:
        return

    pending = _pending_spans.pop(span_id, None)
    if not pending:
        return

    now = _get_timestamp()
    duration_us = now - pending.start_ts

    _events.append(TraceEvent(
        name=pending.name,
        cat=pending.category,
        ph=TracePhase.END,
        ts=now,
        pid=pending.agent_info.process_id,
        tid=pending.agent_info.thread_id,
        args={
            **pending.args,
            "decision": decision,
            "source": source,
            "duration_ms": duration_us / 1000,
        },
    ))


def start_interaction_span(user_prompt: Optional[str] = None) -> str:
    """Start an interaction span (full user request cycle)."""
    if not _is_enabled:
        return ""

    span_id = _generate_span_id()
    agent_info = _get_current_agent_info()
    now = _get_timestamp()

    pending = PendingSpan(
        name="Interaction",
        category="interaction",
        start_ts=now,
        agent_info=agent_info,
        args={"user_prompt_length": len(user_prompt) if user_prompt else None},
    )
    _pending_spans[span_id] = pending

    _events.append(TraceEvent(
        name="Interaction",
        cat="interaction",
        ph=TracePhase.BEGIN,
        ts=now,
        pid=agent_info.process_id,
        tid=agent_info.thread_id,
        args=pending.args,
    ))
    return span_id


def end_interaction_span(span_id: str) -> None:
    """End an interaction span."""
    if not _is_enabled or not span_id:
        return

    pending = _pending_spans.pop(span_id, None)
    if not pending:
        return

    now = _get_timestamp()
    duration_us = now - pending.start_ts

    _events.append(TraceEvent(
        name=pending.name,
        cat=pending.category,
        ph=TracePhase.END,
        ts=now,
        pid=pending.agent_info.process_id,
        tid=pending.agent_info.thread_id,
        args={**pending.args, "duration_ms": duration_us / 1000},
    ))


def emit_instant(
    name: str,
    category: str,
    **kwargs: Any,
) -> None:
    """Emit an instant (marker) event."""
    if not _is_enabled:
        return
    agent_info = _get_current_agent_info()
    _events.append(TraceEvent(
        name=name,
        cat=category,
        ph=TracePhase.INSTANT,
        ts=_get_timestamp(),
        pid=agent_info.process_id,
        tid=agent_info.thread_id,
        args=kwargs if kwargs else None,
    ))


def emit_counter(name: str, values: dict[str, float]) -> None:
    """Emit a counter event for tracking metrics over time."""
    if not _is_enabled:
        return
    agent_info = _get_current_agent_info()
    _events.append(TraceEvent(
        name=name,
        cat="counter",
        ph=TracePhase.COUNTER,
        ts=_get_timestamp(),
        pid=agent_info.process_id,
        tid=agent_info.thread_id,
        args=values,
    ))


def register_agent(
    agent_id: str,
    agent_name: str,
    parent_agent_id: Optional[str] = None,
) -> None:
    """Register a subagent/teammate in the trace."""
    if not _is_enabled:
        return
    info = AgentInfo(
        agent_id=agent_id,
        agent_name=agent_name,
        parent_agent_id=parent_agent_id,
        process_id=_get_process_id_for_agent(agent_id),
        thread_id=_string_to_numeric_hash(agent_name),
    )
    with _lock:
        _agent_registry[agent_id] = info
    _emit_process_metadata(info)


def unregister_agent(agent_id: str) -> None:
    """Unregister an agent to free memory."""
    if not _is_enabled:
        return
    with _lock:
        _agent_registry.pop(agent_id, None)
        _agent_id_to_process_id.pop(agent_id, None)


# ---------------------------------------------------------------------------
# Test / introspection helpers
# ---------------------------------------------------------------------------

def get_events() -> list[TraceEvent]:
    """Return all recorded events (for testing)."""
    with _lock:
        return [*_metadata_events, *_events]


def reset_tracer() -> None:
    """Reset all tracer state (for testing)."""
    global _is_enabled, _trace_path, _start_time_ms, _trace_written
    global _span_id_counter, _process_id_counter

    _stop_write_timer()
    if _stale_cleanup_timer:
        _stale_cleanup_timer.cancel()
        _stale_cleanup_timer = None

    with _lock:
        _metadata_events.clear()
        _events.clear()
        _pending_spans.clear()
        _agent_registry.clear()
        _agent_id_to_process_id.clear()

    _is_enabled = False
    _trace_path = None
    _start_time_ms = 0
    _trace_written = False
    _span_id_counter = 0
    _process_id_counter = 1


async def trigger_write() -> None:
    """Trigger an immediate periodic write (for testing)."""
    await _async_final_write()


def _run_write_sync() -> None:
    _do_periodic_write()


