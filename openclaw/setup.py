"""
Setup Bootstrap - Application Initialization System

Based on Claude Code's setup.ts (487 lines) - the ordered initialization engine.

Core responsibilities:
1. Bootstrap sequence - ordered, dependency-aware initialization
2. Version checking - minimum requirements validation
3. Working directory management - chdir, worktree creation
4. Hooks snapshot - capture hooks config at startup for change detection
5. Background job initialization - parallel startup tasks
6. Analytics sinks setup - event logging infrastructure
7. Permission verification - security context validation
8. UDS messaging server - Unix domain socket for IPC

Design patterns:
- Early return for recovery modes (LOCAL_RECOVERY=1)
- Checkpoint profiling for startup performance analysis
- Hook config snapshot for change detection
- Parallel vs sequential initialization decisions
"""

from __future__ import annotations

import os
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set


class SetupCheckpoint(str, Enum):
    """Named checkpoints for startup profiling."""
    START = "setup_start"
    VERSION_CHECK = "setup_version_check"
    CWD_SET = "setup_cwd_set"
    HOOKS_CAPTURED = "setup_hooks_captured"
    WORKTREE_CREATED = "setup_worktree_created"
    BACKGROUND_JOBS = "setup_background_jobs_launched"
    PREFETCH = "setup_prefetch_done"
    SINKS_INIT = "setup_sinks_init"
    PERMISSION_CHECK = "setup_permission_check"
    COMPLETE = "setup_complete"


@dataclass
class SetupContext:
    """
    Context passed through the setup pipeline.
    
    Carries all configuration and state needed during initialization.
    """
    # Core paths
    cwd: str
    original_cwd: str
    project_root: str
    
    # Configuration
    permission_mode: str
    allow_dangerously_skip_permissions: bool = False
    worktree_enabled: bool = False
    worktree_name: Optional[str] = None
    worktree_pr_number: Optional[int] = None
    tmux_enabled: bool = False
    
    # Session
    custom_session_id: Optional[str] = None
    messaging_socket_path: Optional[str] = None
    
    # State
    is_bare_mode: bool = False
    is_non_interactive: bool = False
    is_docker: bool = False
    is_sandbox: bool = False
    is_root: bool = False
    
    # Worktree info (populated if created)
    worktree_path: Optional[str] = None
    worktree_branch: Optional[str] = None
    
    # Hooks snapshot (captured at startup)
    hooks_snapshot: Optional[Dict[str, Any]] = None
    
    # Timing
    checkpoints: Dict[str, float] = field(default_factory=dict)
    
    def checkpoint(self, name: SetupCheckpoint) -> None:
        self.checkpoints[name.value] = time.time()
    
    def checkpoint_duration(self, name: SetupCheckpoint) -> Optional[float]:
        start = self.checkpoints.get(SetupCheckpoint.START.value, time.time())
        cp = self.checkpoints.get(name.value)
        if cp is None:
            return None
        return cp - start


class SetupHooks:
    """
    Extensible hooks for setup customization.
    
    Allows plugins and extensions to inject initialization steps.
    """
    
    def __init__(self):
        self._pre_checks: List[Callable[[SetupContext], Optional[str]]] = []
        self._post_cwd: List[Callable[[SetupContext], None]] = []
        self._post_worktree: List[Callable[[SetupContext], None]] = []
        self._background_jobs: List[Callable[[SetupContext], None]] = []
        self._final_checks: List[Callable[[SetupContext], Optional[str]]] = []
        self._lock = threading.Lock()
    
    def pre_check(self, fn: Callable[[SetupContext], Optional[str]]) -> None:
        """Register a pre-check that can return error message."""
        with self._lock:
            self._pre_checks.append(fn)
    
    def post_cwd(self, fn: Callable[[SetupContext], None]) -> None:
        """Register a hook called after CWD is set."""
        with self._lock:
            self._post_cwd.append(fn)
    
    def post_worktree(self, fn: Callable[[SetupContext], None]) -> None:
        """Register a hook called after worktree creation."""
        with self._lock:
            self._post_worktree.append(fn)
    
    def background_job(self, fn: Callable[[SetupContext], None]) -> None:
        """Register a background job to run during initialization."""
        with self._lock:
            self._background_jobs.append(fn)
    
    def final_check(self, fn: Callable[[SetupContext], Optional[str]]) -> None:
        """Register a final check that can return error message."""
        with self._lock:
            self._final_checks.append(fn)
    
    def run_pre_checks(self, ctx: SetupContext) -> Optional[str]:
        for fn in self._pre_checks:
            try:
                result = fn(ctx)
                if result:
                    return result
            except Exception as e:
                return f"Pre-check {fn.__name__} failed: {e}"
        return None
    
    def run_post_cwd(self, ctx: SetupContext) -> None:
        for fn in self._post_cwd:
            try:
                fn(ctx)
            except Exception:
                pass  # Log but don't fail setup
    
    def run_post_worktree(self, ctx: SetupContext) -> None:
        for fn in self._post_worktree:
            try:
                fn(ctx)
            except Exception:
                pass
    
    def run_background_jobs(self, ctx: SetupContext) -> List[threading.Thread]:
        threads = []
        for fn in self._background_jobs:
            t = threading.Thread(target=self._run_bg_job, args=(fn, ctx), daemon=True)
            t.start()
            threads.append(t)
        return threads
    
    def _run_bg_job(self, fn: Callable[[SetupContext], None], ctx: SetupContext) -> None:
        try:
            fn(ctx)
        except Exception:
            pass
    
    def run_final_checks(self, ctx: SetupContext) -> Optional[str]:
        for fn in self._final_checks:
            try:
                result = fn(ctx)
                if result:
                    return result
            except Exception as e:
                return f"Final check {fn.__name__} failed: {e}"
        return None


# Global hooks instance
_setup_hooks = SetupHooks()


def get_setup_hooks() -> SetupHooks:
    """Get the global setup hooks instance."""
    return _setup_hooks


def register_setup_hook(
    hook_type: str,
    fn: Callable,
) -> None:
    """Register a setup hook by type."""
    hooks = get_setup_hooks()
    if hook_type == "pre_check":
        hooks.pre_check(fn)
    elif hook_type == "post_cwd":
        hooks.post_cwd(fn)
    elif hook_type == "post_worktree":
        hooks.post_worktree(fn)
    elif hook_type == "background_job":
        hooks.background_job(fn)
    elif hook_type == "final_check":
        hooks.final_check(fn)


class SetupError(Exception):
    """Setup failure with exit code."""
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


def check_minimum_version(min_version: tuple[int, int]) -> Optional[str]:
    """
    Check if Python version meets minimum requirement.
    
    Returns error message if check fails, None if OK.
    """
    major, minor = sys.version_info[:2]
    req_major, req_minor = min_version
    
    if major < req_major or (major == req_major and minor < req_minor):
        return (
            f"Python {req_major}.{req_minor}+ required, "
            f"but found {major}.{minor}.{sys.version_info[2]}"
        )
    return None


def check_environment_safety(ctx: SetupContext) -> Optional[str]:
    """
    Verify environment is safe for operation.
    
    Checks:
    - Not running as root (unless sandbox)
    - Docker/sandbox detection
    - Internet access in sandboxed environments
    """
    # Root check
    if hasattr(os, "getuid") and os.getuid() == 0:
        if not ctx.is_sandbox and os.environ.get("CLAUDE_CODE_BUBBLEWRAP") != "1":
            return (
                "Cannot run as root. Use a sandbox environment or set "
                "IS_SANDBOX=1 if running in a protected container."
            )
    
    # Docker check
    if ctx.is_docker:
        try:
            # Check for internet access in docker
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            has_internet = True
        except Exception:
            has_internet = False
        
        is_sandboxed = ctx.is_docker or ctx.is_sandbox
        if (
            os.environ.get("USER_TYPE") == "ant"
            and not os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "local-agent"
            and not os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "claude-desktop"
            and is_sandboxed
            and has_internet
        ):
            return (
                "Security: --dangerously-skip-permissions requires no internet access "
                "in Docker/sandbox containers."
            )
    
    return None


def capture_hooks_snapshot(cwd: str) -> Dict[str, Any]:
    """
    Capture hooks configuration snapshot for change detection.
    
    This allows detecting if hooks are modified during operation,
    which could affect security or behavior.
    """
    import hashlib
    import json
    
    snapshot = {
        "timestamp": time.time(),
        "cwd": cwd,
        "hooks": {},
    }
    
    # Check common hook locations
    hook_paths = [
        Path(cwd) / ".git" / "hooks",
        Path(cwd) / ".claude" / "hooks",
        Path.home() / ".claude" / "hooks",
    ]
    
    for hook_dir in hook_paths:
        if hook_dir.exists() and hook_dir.is_dir():
            hook_files = {}
            for f in hook_dir.iterdir():
                if f.is_file():
                    content = f.read_bytes()
                    hook_files[f.name] = {
                        "size": len(content),
                        "hash": hashlib.md5(content).hexdigest(),
                    }
            if hook_files:
                snapshot["hooks"][str(hook_dir)] = hook_files
    
    return snapshot


def detect_docker() -> bool:
    """Detect if running in Docker."""
    if Path("/.dockerenv").exists():
        return True
    try:
        with open("/proc/1/cgroup", "r") as f:
            return "docker" in f.read().lower()
    except Exception:
        return False


def detect_sandbox() -> bool:
    """Detect if running in a sandbox environment."""
    return (
        detect_docker()
        or os.environ.get("IS_SANDBOX") == "1"
        or os.environ.get("CLAUDE_CODE_BUBBLEWRAP") == "1"
    )


def is_bare_mode() -> bool:
    """Check if running in bare/scripted mode (no interactive features)."""
    return os.environ.get("CLAUDE_CODE_BARE") == "1" or os.environ.get("SIMPLE") == "1"


def is_non_interactive_session() -> bool:
    """Check if running in a non-interactive session."""
    return not sys.stdin.isatty()


async def run_setup(
    cwd: str,
    permission_mode: str,
    allow_dangerously_skip_permissions: bool = False,
    worktree_enabled: bool = False,
    worktree_name: Optional[str] = None,
    worktree_pr_number: Optional[int] = None,
    tmux_enabled: bool = False,
    custom_session_id: Optional[str] = None,
    messaging_socket_path: Optional[str] = None,
) -> SetupContext:
    """
    Run the complete setup bootstrap sequence.
    
    Returns SetupContext with all state populated.
    Raises SetupError on failure.
    """
    ctx = SetupContext(
        cwd=cwd,
        original_cwd=cwd,
        project_root=cwd,
        permission_mode=permission_mode,
        allow_dangerously_skip_permissions=allow_dangerously_skip_permissions,
        worktree_enabled=worktree_enabled,
        worktree_name=worktree_name,
        worktree_pr_number=worktree_pr_number,
        tmux_enabled=tmux_enabled,
        custom_session_id=custom_session_id,
        messaging_socket_path=messaging_socket_path,
        is_bare_mode=is_bare_mode(),
        is_non_interactive=is_non_interactive_session(),
        is_docker=detect_docker(),
        is_sandbox=detect_sandbox(),
    )
    ctx.checkpoint(SetupCheckpoint.START)
    
    # === 1. Version Check ===
    version_error = check_minimum_version((3, 9))
    if version_error:
        raise SetupError(version_error)
    ctx.checkpoint(SetupCheckpoint.VERSION_CHECK)
    
    # === 2. Run Pre-Checks ===
    error = _setup_hooks.run_pre_checks(ctx)
    if error:
        raise SetupError(error)
    
    # === 3. Set CWD ===
    os.chdir(cwd)
    ctx.cwd = cwd
    ctx.original_cwd = cwd
    ctx.project_root = cwd
    ctx.checkpoint(SetupCheckpoint.CWD_SET)
    
    # === 4. Run Post-CWD Hooks ===
    _setup_hooks.run_post_cwd(ctx)
    
    # === 5. Early Return for Recovery Mode ===
    if os.environ.get("CLAUDE_CODE_LOCAL_RECOVERY") == "1":
        ctx.checkpoint(SetupCheckpoint.COMPLETE)
        return ctx
    
    # === 6. Capture Hooks Snapshot ===
    ctx.hooks_snapshot = capture_hooks_snapshot(cwd)
    ctx.checkpoint(SetupCheckpoint.HOOKS_CAPTURED)
    
    # === 7. Worktree Creation ===
    if worktree_enabled:
        ctx = await _create_worktree(ctx)
        ctx.checkpoint(SetupCheckpoint.WORKTREE_CREATED)
        _setup_hooks.run_post_worktree(ctx)
    
    # === 8. Background Jobs ===
    bg_threads = _setup_hooks.run_background_jobs(ctx)
    ctx.checkpoint(SetupCheckpoint.BACKGROUND_JOBS)
    
    # === 9. Initialize Analytics Sinks ===
    _init_sinks(ctx)
    ctx.checkpoint(SetupCheckpoint.SINKS_INIT)
    
    # === 10. Permission Check ===
    if allow_dangerously_skip_permissions or permission_mode == "bypassPermissions":
        error = check_environment_safety(ctx)
        if error:
            raise SetupError(error, exit_code=1)
    ctx.checkpoint(SetupCheckpoint.PERMISSION_CHECK)
    
    # === 11. Wait for Background Jobs ===
    for t in bg_threads:
        t.join(timeout=5.0)  # Don't block forever
    
    # === 12. Run Final Checks ===
    error = _setup_hooks.run_final_checks(ctx)
    if error:
        raise SetupError(error)
    
    ctx.checkpoint(SetupCheckpoint.COMPLETE)
    return ctx


async def _create_worktree(ctx: SetupContext) -> SetupContext:
    """Create a worktree for session isolation."""
    # Check if git repository
    git_root = _find_git_root(ctx.cwd)
    if not git_root and not _has_worktree_create_hook():
        raise SetupError(
            f"Worktree requires git repository at {ctx.cwd}, "
            "or configure a WorktreeCreate hook."
        )
    
    # Determine worktree name
    if ctx.worktree_pr_number:
        slug = f"pr-{ctx.worktree_pr_number}"
    elif ctx.worktree_name:
        slug = ctx.worktree_name
    else:
        slug = _generate_session_slug(ctx.custom_session_id or "session")
    
    # Create worktree
    branch_name = f"claude/{slug}"
    
    try:
        worktree_path = await _create_git_worktree(
            git_root or ctx.cwd,
            branch_name,
            ctx.tmux_enabled,
        )
        ctx.worktree_path = worktree_path
        ctx.worktree_branch = branch_name
        
        # Switch to worktree directory
        os.chdir(worktree_path)
        ctx.cwd = worktree_path
        ctx.project_root = worktree_path
        
    except Exception as e:
        raise SetupError(f"Failed to create worktree: {e}")
    
    return ctx


def _find_git_root(path: str) -> Optional[str]:
    """Find git repository root."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _has_worktree_create_hook() -> bool:
    """Check if WorktreeCreate hook is configured."""
    # Check environment or settings
    return os.environ.get("CLAUDE_CODE_WORKTREE_HOOK") == "1"


async def _create_git_worktree(
    repo_root: str,
    branch_name: str,
    tmux_enabled: bool,
) -> str:
    """Create a git worktree and return its path."""
    import subprocess
    
    # Determine worktree directory
    worktrees_base = Path(repo_root).parent / f"{Path(repo_root).name}-worktrees"
    worktree_path = worktrees_base / branch_name.replace("/", "-")
    
    # Create worktree
    result = subprocess.run(
        ["git", "worktree", "add", "-b", branch_name, str(worktree_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"git worktree add failed: {result.stderr}")
    
    return str(worktree_path)


def _generate_session_slug(session_id: str) -> str:
    """Generate a URL-safe slug for a session."""
    import hashlib
    slug = hashlib.md5(session_id.encode()).hexdigest()[:8]
    return f"session-{slug}"


def _init_sinks(ctx: SetupContext) -> None:
    """Initialize analytics and logging sinks."""
    # Import analytics
    try:
        from openclaw import analytics
        analytics.init_sinks()
    except ImportError:
        pass


class SetupProfiler:
    """
    Startup performance profiler.
    
    Tracks checkpoints and can emit structured timing data
    for startup performance analysis.
    """
    
    def __init__(self):
        self._checkpoints: Dict[str, float] = {SetupCheckpoint.START.value: time.time()}
        self._lock = threading.Lock()
    
    def checkpoint(self, name: SetupCheckpoint) -> None:
        with self._lock:
            self._checkpoints[name.value] = time.time()
    
    def get_timings(self) -> Dict[str, float]:
        """Get all timings relative to start."""
        with self._lock:
            start = self._checkpoints.get(SetupCheckpoint.START.value, 0)
            return {
                name: ts - start
                for name, ts in self._checkpoints.items()
            }
    
    def emit_diagnostics(self) -> Dict[str, Any]:
        """Emit structured diagnostics for logging."""
        timings = self.get_timings()
        return {
            "setup_timings": {
                k: f"{v*1000:.1f}ms"
                for k, v in timings.items()
            },
            "total_ms": timings.get(SetupCheckpoint.COMPLETE.value, 0) * 1000,
        }


# Global profiler
_profiler = SetupProfiler()


def get_profiler() -> SetupProfiler:
    """Get the global setup profiler."""
    return _profiler


def profile_checkpoint(name: SetupCheckpoint) -> None:
    """Record a profiling checkpoint."""
    _profiler.checkpoint(name)


# === Convenience Functions ===

async def quick_setup(cwd: str = ".") -> SetupContext:
    """
    Quick setup with defaults.
    
    For scripted/non-interactive use cases.
    """
    return await run_setup(
        cwd=cwd,
        permission_mode="ask",
        allow_dangerously_skip_permissions=False,
    )


async def worktree_setup(
    cwd: str,
    session_name: Optional[str] = None,
    tmux_enabled: bool = False,
) -> SetupContext:
    """
    Setup with worktree isolation.
    
    Creates an isolated git worktree for the session.
    """
    return await run_setup(
        cwd=cwd,
        permission_mode="ask",
        worktree_enabled=True,
        worktree_name=session_name,
        tmux_enabled=tmux_enabled,
    )
