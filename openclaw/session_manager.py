"""
Session Manager - Multi-Session Lifecycle Management System

Based on Claude Code's bridgeMain.ts (2999 lines) - the core session orchestration engine.
Provides:
- Multi-session lifecycle (spawn/kill/timeout/heartbeat)
- Exponential backoff with jitter for resilient connections
- Capacity management with at-capacity wake signals
- Token refresh scheduler for proactive auth
- Worktree isolation per session
- Graceful shutdown with SIGTERM→SIGKILL

Key design patterns extracted:
1. BackoffConfig: configurable initial/cap/give-up ms for conn and general errors
2. SessionHandle: typed handle with done promise, kill, forceKill, updateAccessToken
3. CapacityWake: event-based early wake when session completes
4. TokenRefreshScheduler: proactive JWT refresh before expiry
5. TrackCleanup: pending promise tracking for graceful shutdown
"""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class SessionStatus(str, Enum):
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    RESULT = "result"
    ERROR = "error"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    TIMED_OUT = "timed_out"


class SpawnMode(str, Enum):
    SINGLE_SESSION = "single-session"
    SAME_DIR = "same-dir"
    WORKTREE = "worktree"


@dataclass
class BackoffConfig:
    """Exponential backoff configuration for connection/general errors."""
    conn_initial_ms: int = 2_000
    conn_cap_ms: int = 120_000  # 2 minutes
    conn_give_up_ms: int = 600_000  # 10 minutes
    general_initial_ms: int = 500
    general_cap_ms: int = 30_000
    general_give_up_ms: int = 600_000  # 10 minutes
    shutdown_grace_ms: int = 30_000
    stop_work_base_delay_ms: int = 1_000

    @classmethod
    def default(cls) -> BackoffConfig:
        return cls()


@dataclass
class Activity:
    """Session activity state for status display."""
    type: str  # tool_start, result, error, user, assistant, etc.
    summary: str = ""
    detail: str = ""


@dataclass
class SessionHandle:
    """
    Handle for a managed session process.
    
    Provides:
    - done: asyncio.Future-like event that resolves when session ends
    - kill(): graceful SIGTERM
    - forceKill(): SIGKILL after grace period
    - updateAccessToken(): update OAuth token for reconnect
    - currentActivity: current activity for status display
    - activities: recent activity history (last N)
    """
    session_id: str
    process: subprocess.Popen
    sdk_url: str
    access_token: str
    worktree_path: Optional[str] = None
    worktree_branch: Optional[str] = None
    
    # Internal state
    _done_event: threading.Event = field(default_factory=threading.Event)
    _exit_code: Optional[int] = field(default=None)
    _current_activity: Optional[Activity] = field(default=None)
    _activities: list[Activity] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _grace_timer: Optional[threading.Timer] = field(default=None)
    
    # Config
    shutdown_grace_ms: int = 30_000

    @property
    def done(self) -> threading.Event:
        """Event that is set when session completes."""
        return self._done_event

    @property
    def exit_code(self) -> Optional[int]:
        return self._exit_code

    @property
    def current_activity(self) -> Optional[Activity]:
        return self._current_activity

    @property
    def activities(self) -> list[Activity]:
        return self._activities.copy()

    def update_activity(self, activity: Activity) -> None:
        """Update current activity and append to history."""
        with self._lock:
            self._current_activity = activity
            # Keep last 50 activities
            self._activities.append(activity)
            if len(self._activities) > 50:
                self._activities = self._activities[-50:]

    def update_access_token(self, token: str) -> None:
        """Update the OAuth access token for reconnect."""
        with self._lock:
            self.access_token = token

    def kill(self, grace_ms: Optional[int] = None) -> None:
        """
        Graceful termination: send SIGTERM, wait for grace period,
        then force kill if still alive.
        """
        grace = grace_ms or self.shutdown_grace_ms
        
        # Send SIGTERM
        try:
            self.process.terminate()
        except ProcessLookupError:
            # Already dead
            self._exit_code = self.process.poll()
            self._done_event.set()
            return
        
        # Schedule force kill
        def force_kill():
            try:
                self.process.kill()
            except ProcessLookupError:
                pass
            self._exit_code = -9
            self._done_event.set()
        
        self._grace_timer = threading.Timer(grace / 1000, force_kill)
        self._grace_timer.daemon = True
        self._grace_timer.start()

    def force_kill(self) -> None:
        """Immediate SIGKILL."""
        if self._grace_timer:
            self._grace_timer.cancel()
            self._grace_timer = None
        try:
            self.process.kill()
        except ProcessLookupError:
            pass
        self._exit_code = -9
        self._done_event.set()

    def poll(self) -> Optional[int]:
        """Check if process has exited, return exit code or None."""
        return self.process.poll()

    def wait(self, timeout: Optional[float] = None) -> bool:
        """Wait for session to complete, returns True if done."""
        return self._done_event.wait(timeout=timeout)


@dataclass
class SpawnOpts:
    """Options for spawning a new session."""
    session_id: str
    sdk_url: str
    access_token: str
    use_ccr_v2: bool = False
    worker_epoch: Optional[int] = None
    on_first_user_message: Optional[Callable[[str], None]] = None
    worktree_path: Optional[str] = None
    worktree_branch: Optional[str] = None
    debug_file: Optional[str] = None


class SessionManager:
    """
    Multi-session lifecycle manager with backoff, heartbeat, and graceful shutdown.
    
    Core responsibilities:
    1. Track active sessions and their states
    2. Manage exponential backoff for connection errors
    3. Handle capacity limits and wake signals
    4. Coordinate graceful shutdown of all sessions
    5. Track pending cleanup operations
    """
    
    def __init__(
        self,
        max_sessions: int = 32,
        spawn_mode: SpawnMode = SpawnMode.SAME_DIR,
        backoff_config: Optional[BackoffConfig] = None,
        shutdown_grace_ms: int = 30_000,
    ):
        self.max_sessions = max_sessions
        self.spawn_mode = spawn_mode
        self.backoff_config = backoff_config or BackoffConfig.default()
        self.shutdown_grace_ms = shutdown_grace_ms
        
        # Session tracking
        self._active_sessions: dict[str, SessionHandle] = {}
        self._session_start_times: dict[str, float] = {}
        self._session_work_ids: dict[str, str] = {}
        self._session_ingress_tokens: dict[str, str] = {}
        self._session_timers: dict[str, threading.Timer] = {}
        self._completed_work_ids: set[str] = set()
        self._worktrees: dict[str, dict[str, Any]] = {}
        self._titled_sessions: set[str] = set()
        
        # Backoff state
        self._conn_backoff = 0
        self._general_backoff = 0
        self._conn_error_start: Optional[float] = None
        self._general_error_start: Optional[float] = None
        
        # Capacity wake
        self._capacity_wake = threading.Event()
        
        # Pending cleanup promises
        self._pending_cleanups: set[threading.Event] = set()
        
        # Shutdown flag
        self._shutdown = threading.Event()
        
        # Lock for thread safety
        self._lock = threading.RLock()

    @property
    def active_sessions(self) -> dict[str, SessionHandle]:
        with self._lock:
            return self._active_sessions.copy()

    @property
    def session_count(self) -> int:
        return len(self._active_sessions)

    @property
    def at_capacity(self) -> bool:
        return len(self._active_sessions) >= self.max_sessions

    def add_session(self, handle: SessionHandle, work_id: str = "", ingress_token: str = "") -> None:
        """Register a new active session."""
        with self._lock:
            self._active_sessions[handle.session_id] = handle
            self._session_start_times[handle.session_id] = time.time()
            if work_id:
                self._session_work_ids[handle.session_id] = work_id
            if ingress_token:
                self._session_ingress_tokens[handle.session_id] = ingress_token

    def remove_session(self, session_id: str) -> Optional[SessionHandle]:
        """Remove a session from active tracking."""
        with self._lock:
            handle = self._active_sessions.pop(session_id, None)
            self._session_start_times.pop(session_id, None)
            self._session_work_ids.pop(session_id, None)
            self._session_ingress_tokens.pop(session_id, None)
            self._session_ingress_tokens.pop(session_id, None)
            
            # Clear timeout timer
            timer = self._session_timers.pop(session_id, None)
            if timer:
                timer.cancel()
            
            # Wake capacity waiters
            self._capacity_wake.set()
            self._capacity_wake.clear()
            
            return handle

    def get_session(self, session_id: str) -> Optional[SessionHandle]:
        return self._active_sessions.get(session_id)

    def get_work_id(self, session_id: str) -> Optional[str]:
        return self._session_work_ids.get(session_id)

    def get_ingress_token(self, session_id: str) -> Optional[str]:
        return self._session_ingress_tokens.get(session_id)

    def mark_work_completed(self, work_id: str) -> None:
        """Mark a work item as completed to skip re-delivery."""
        self._completed_work_ids.add(work_id)

    def is_work_completed(self, work_id: str) -> bool:
        return work_id in self._completed_work_ids

    def add_timeout(self, session_id: str, timeout_ms: int, callback: Callable[[], None]) -> None:
        """Set a per-session timeout watchdog."""
        timer = threading.Timer(timeout_ms / 1000, callback)
        timer.daemon = True
        with self._lock:
            # Clear existing timer
            existing = self._session_timers.get(session_id)
            if existing:
                existing.cancel()
            self._session_timers[session_id] = timer
        timer.start()

    def track_cleanup(self, event: threading.Event) -> None:
        """Track a pending cleanup operation."""
        self._pending_cleanups.add(event)
        event.add_done_callback(lambda e: self._pending_cleanups.discard(e))

    def wait_for_capacity(self, timeout: Optional[float] = None) -> bool:
        """Wait until a session slot is available."""
        while self.at_capacity and not self._shutdown.is_set():
            if not self._capacity_wake.wait(timeout=timeout or 1.0):
                return False
        return not self._shutdown.is_set()

    def set_shutdown(self) -> None:
        """Signal shutdown - stops new session creation."""
        self._shutdown.set()
        self._capacity_wake.set()  # Wake any waiters

    @property
    def is_shutting_down(self) -> bool:
        return self._shutdown.is_set()

    async def wait_for_cleanups(self, timeout: Optional[float] = None) -> None:
        """Wait for all pending cleanup operations."""
        start = time.time()
        remaining = self._pending_cleanups.copy()
        while remaining and (timeout is None or time.time() - start < timeout):
            wait_timeout = (timeout - (time.time() - start)) if timeout else None
            for event in list(remaining):
                if event.wait(timeout=wait_timeout or 0.1):
                    remaining.discard(event)
            remaining = self._pending_cleanups.copy()

    # === Backoff Management ===
    
    def reset_backoff(self) -> None:
        """Reset backoff state after successful operation."""
        self._conn_backoff = 0
        self._general_backoff = 0
        self._conn_error_start = None
        self._general_error_start = None

    def check_connection_give_up(self) -> bool:
        """Check if connection backoff has exceeded give-up threshold."""
        if self._conn_error_start is None:
            return False
        elapsed = (time.time() - self._conn_error_start) * 1000
        return elapsed >= self.backoff_config.conn_give_up_ms

    def check_general_give_up(self) -> bool:
        """Check if general backoff has exceeded give-up threshold."""
        if self._general_error_start is None:
            return False
        elapsed = (time.time() - self._general_error_start) * 1000
        return elapsed >= self.backoff_config.general_give_up_ms

    def record_connection_error(self) -> float:
        """Record a connection error, return the next backoff delay."""
        now = time.time()
        if self._conn_error_start is None:
            self._conn_error_start = now
        
        self._conn_backoff = self._next_backoff_delay(
            self._conn_backoff,
            self.backoff_config.conn_initial_ms,
            self.backoff_config.conn_cap_ms,
        )
        return self._conn_backoff

    def record_general_error(self) -> float:
        """Record a general error, return the next backoff delay."""
        now = time.time()
        if self._general_error_start is None:
            self._general_error_start = now
        
        self._general_backoff = self._next_backoff_delay(
            self._general_backoff,
            self.backoff_config.general_initial_ms,
            self.backoff_config.general_cap_ms,
        )
        return self._general_backoff

    def _next_backoff_delay(self, current: int, initial: int, cap: int) -> int:
        """Compute next exponential backoff delay with ±25% jitter."""
        if current == 0:
            delay = initial
        else:
            delay = min(current * 2, cap)
        
        # Add ±25% jitter
        import random
        jitter_range = delay * 0.25
        delay = delay + jitter_range * (2 * random.random() - 1)
        return max(0, int(delay))

    def connection_backoff_sleep_time(self) -> float:
        """Get current connection backoff sleep time in seconds."""
        return self._conn_backoff / 1000

    def general_backoff_sleep_time(self) -> float:
        """Get current general backoff sleep time in seconds."""
        return self._general_backoff / 1000

    # === Graceful Shutdown ===

    async def graceful_shutdown(self) -> dict[str, Any]:
        """
        Graceful shutdown of all sessions.
        
        1. Signal shutdown
        2. Send SIGTERM to all sessions
        3. Wait for grace period
        4. SIGKILL any remaining
        5. Clean up worktrees
        6. Stop all timers
        
        Returns summary of cleanup results.
        """
        self.set_shutdown()
        results = {
            "sessions_killed": 0,
            "sessions_force_killed": 0,
            "worktrees_cleaned": 0,
            "timers_cleared": 0,
        }
        
        with self._lock:
            sessions = list(self._active_sessions.items())
        
        if not sessions:
            return results
        
        # Send SIGTERM to all
        for session_id, handle in sessions:
            try:
                handle.kill(self.shutdown_grace_ms)
                results["sessions_killed"] += 1
            except Exception:
                pass
        
        # Wait for grace period
        grace_end = time.time() + self.shutdown_grace_ms / 1000
        for session_id, handle in sessions:
            remaining = grace_end - time.time()
            if remaining > 0:
                handle.wait(timeout=remaining)
        
        # Force kill any remaining
        for session_id, handle in sessions:
            if not handle.done.is_set():
                try:
                    handle.force_kill()
                    results["sessions_force_killed"] += 1
                except Exception:
                    pass
        
        # Clear timers
        with self._lock:
            for timer in self._session_timers.values():
                timer.cancel()
            results["timers_cleared"] = len(self._session_timers)
            self._session_timers.clear()
        
        # Clean up worktrees
        with self._lock:
            worktrees = list(self._worktrees.items())
        
        for session_id, wt_info in worktrees:
            try:
                # Import here to avoid circular imports
                from openclaw.worktree import remove_worktree
                remove_worktree(
                    wt_info.get("path"),
                    wt_info.get("branch"),
                    wt_info.get("git_root"),
                )
                results["worktrees_cleaned"] += 1
            except Exception:
                pass
        
        return results


class TokenRefreshScheduler:
    """
    Proactive token refresh scheduler.
    
    Schedules refresh timers before JWT expires to prevent auth failures.
    On refresh callback:
    - v1: delivers OAuth token directly to session
    - v2: calls reconnectSession to trigger server re-dispatch
    """
    
    def __init__(
        self,
        get_access_token: Callable[[], Optional[str]],
        on_refresh: Callable[[str, str], None],  # session_id, oauth_token
        label: str = "default",
    ):
        self.get_access_token = get_access_token
        self.on_refresh = on_refresh
        self.label = label
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
    
    def schedule(self, session_id: str, token: str, expires_in_seconds: int = 14100) -> None:
        """
        Schedule a token refresh.
        
        Default expires_in_seconds is 3h55m ( CCR session ingress JWT TTL).
        Schedules refresh 5 minutes before expiry.
        """
        refresh_offset = 300  # 5 minutes before expiry
        delay = max(1, expires_in_seconds - refresh_offset)
        
        with self._lock:
            # Cancel existing timer
            existing = self._timers.get(session_id)
            if existing:
                existing.cancel()
            
            # Schedule new refresh
            def do_refresh():
                token = self.get_access_token()
                if token:
                    self.on_refresh(session_id, token)
                with self._lock:
                    self._timers.pop(session_id, None)
            
            timer = threading.Timer(delay, do_refresh)
            timer.daemon = True
            self._timers[session_id] = timer
            timer.start()

    def cancel(self, session_id: str) -> None:
        """Cancel refresh timer for a session."""
        with self._lock:
            timer = self._timers.pop(session_id, None)
            if timer:
                timer.cancel()

    def cancel_all(self) -> None:
        """Cancel all refresh timers."""
        with self._lock:
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()


def format_duration(ms: float) -> str:
    """Format milliseconds as human-readable duration."""
    seconds = ms / 1000
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)}m {int(seconds % 60)}s"
    hours = minutes / 60
    return f"{int(hours)}h {int(minutes % 60)}m"


def add_jitter(ms: int, jitter_pct: float = 0.25) -> int:
    """Add ±jitter_pct random jitter to a delay value."""
    import random
    jitter_range = ms * jitter_pct
    return max(0, int(ms + jitter_range * (2 * random.random() - 1)))


# === Connection Error Detection ===

CONNECTION_ERROR_CODES = {
    "ECONNREFUSED",
    "ECONNRESET",
    "ETIMEDOUT",
    "ENETUNREACH",
    "EHOSTUNREACH",
}


def is_connection_error(err: Exception) -> bool:
    """Detect connection-related OS errors."""
    if hasattr(err, "errno"):
        import errno
        try:
            code = errno.errorcode.get(err.errno, "")
            if code in CONNECTION_ERROR_CODES:
                return True
        except Exception:
            pass
    if hasattr(err, "code") and isinstance(err.code, str):
        return err.code in CONNECTION_ERROR_CODES
    return False


def is_server_error(err: Exception) -> bool:
    """Detect HTTP 5xx errors (code: 'ERR_BAD_RESPONSE')."""
    return hasattr(err, "code") and err.code == "ERR_BAD_RESPONSE"
