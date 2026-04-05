"""
Startup profiling utility for measuring and reporting time spent in various
initialization phases.

Two modes:
1. Sampled logging: 100% of ant users, 0.1% of external users - logs phases
2. Detailed profiling: CLAUDE_CODE_PROFILE_STARTUP=1 - full report with memory snapshots

Uses Python's time.perf_counter for high-resolution timing measurement.
"""

import os
import time
import tracemalloc
import random
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any


class StartupProfiler:
    """
    Startup profiling utility for measuring initialization phases.
    
    Two modes:
    - Sampled: A percentage of sessions log to analytics
    - Detailed: Full report with memory snapshots when env var is set
    """
    
    def __init__(
        self,
        detailed_env_var: str = "CLAUDE_CODE_PROFILE_STARTUP",
        sample_rate: float = 0.005,
    ):
        self.detailed_env_var = detailed_env_var
        self.sample_rate = sample_rate
        
        # Module-level state - decided once at instantiation
        self._detailed_profiling = self._is_detailed_profiling()
        self._sampled = self._should_sample()
        self._should_profile = self._detailed_profiling or self._sampled
        
        # Track marks: name -> (start_time, memory_snapshot)
        self._marks: List[Tuple[str, float, Optional[Dict[str, int]]]] = []
        self._memory_snapshots: List[Optional[Dict[str, int]]] = []
        self._reported = False
        
        # Phase definitions: phase_name -> (start_checkpoint, end_checkpoint)
        self.PHASE_DEFINITIONS = {
            "import_time": ("cli_entry", "main_imports_loaded"),
            "init_time": ("init_function_start", "init_function_end"),
            "settings_time": ("eagerLoadSettings_start", "eagerLoadSettings_end"),
            "total_time": ("cli_entry", "main_after_run"),
        }
        
        # Record initial checkpoint if profiling is enabled
        if self._should_profile:
            self.checkpoint("profiler_initialized")
    
    def _is_detailed_profiling(self) -> bool:
        """Check if detailed profiling is enabled via environment variable."""
        return os.environ.get(self.detailed_env_var, "").lower() in ("1", "true", "yes")
    
    def _should_sample(self) -> bool:
        """Determine if this session should be sampled for analytics."""
        # 100% for internal users (USER_TYPE=ant), sample_rate% for external
        user_type = os.environ.get("USER_TYPE", "")
        if user_type == "ant":
            return True
        return random.random() < self.sample_rate
    
    def is_detailed_profiling_enabled(self) -> bool:
        """Check if detailed profiling is currently enabled."""
        return self._detailed_profiling
    
    def should_profile(self) -> bool:
        """Check if profiling is active (either detailed or sampled)."""
        return self._should_profile
    
    def checkpoint(self, name: str) -> None:
        """
        Record a checkpoint with the given name.
        Captures both timestamp and optional memory snapshot.
        """
        if not self._should_profile:
            return
        
        # Use relative time from first mark for cleaner output
        current_time = time.perf_counter()
        memory_info = None
        
        # Only capture memory when detailed profiling is enabled
        if self._detailed_profiling:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            current, peak = tracemalloc.get_traced_memory()
            memory_info = {
                "current_bytes": current,
                "peak_bytes": peak,
            }
        
        self._marks.append((name, current_time, memory_info))
        self._memory_snapshots.append(memory_info)
    
    def get_elapsed_ms(self, name: str) -> Optional[float]:
        """Get elapsed time in ms since a named checkpoint."""
        for i, (mark_name, start_time, _) in enumerate(self._marks):
            if mark_name == name:
                if i == 0:
                    return 0.0
                prev_time = self._marks[i - 1][1]
                return (start_time - prev_time) * 1000
        return None
    
    def get_absolute_time_ms(self, name: str) -> Optional[float]:
        """Get absolute time in ms from process start for a named checkpoint."""
        for mark_name, start_time, _ in self._marks:
            if mark_name == name:
                return start_time * 1000
        return None
    
    def _format_ms(self, ms: float) -> str:
        """Format milliseconds for display."""
        if ms < 1000:
            return f"{ms:>6.1f}ms"
        return f"{ms/1000:>6.2f}s"
    
    def _format_memory(self, mem: Optional[Dict[str, int]]) -> str:
        """Format memory info for display."""
        if mem is None:
            return " " * 25
        current_mb = mem["current_bytes"] / (1024 * 1024)
        peak_mb = mem["peak_bytes"] / (1024 * 1024)
        return f"{current_mb:>6.1f}MB p={peak_mb:>5.1f}MB"
    
    def _format_timeline_line(
        self,
        start_time_ms: float,
        elapsed_ms: float,
        name: str,
        memory: Optional[Dict[str, int]],
        name_width: int = 40,
    ) -> str:
        """Format a single timeline line for the report."""
        time_str = self._format_ms(elapsed_ms)
        total_str = self._format_ms(start_time_ms)
        mem_str = self._format_memory(memory)
        return f"  {total_str}  +{time_str}  {name[:name_width]:<{name_width}}  {mem_str}"
    
    def get_report(self) -> str:
        """Get a formatted report of all checkpoints."""
        if not self._detailed_profiling:
            return "Startup profiling not enabled (set CLAUDE_CODE_PROFILE_STARTUP=1)"
        
        if not self._marks:
            return "No profiling checkpoints recorded"
        
        lines = []
        lines.append("=" * 80)
        lines.append("STARTUP PROFILING REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Use first mark as baseline for relative times
        baseline = self._marks[0][1] if self._marks else 0
        prev_time_ms = 0.0
        for i, (name, start_time, memory) in enumerate(self._marks):
            start_ms = (start_time - baseline) * 1000
            elapsed_ms = start_ms - prev_time_ms
            lines.append(self._format_timeline_line(start_ms, elapsed_ms, name, memory))
            prev_time_ms = start_ms
        
        last_mark = self._marks[-1]
        total_ms = (last_mark[1] - baseline) * 1000
        lines.append("")
        lines.append(f"Total startup time: {self._format_ms(total_ms)}")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def get_phase_durations(self) -> Dict[str, Optional[float]]:
        """Compute durations for all defined phases."""
        # Build checkpoint lookup
        checkpoint_times = {}
        for name, start_time, _ in self._marks:
            checkpoint_times[name] = start_time * 1000  # Convert to ms
        
        # Compute phase durations
        durations = {}
        for phase_name, (start_cp, end_cp) in self.PHASE_DEFINITIONS.items():
            start_time = checkpoint_times.get(start_cp)
            end_time = checkpoint_times.get(end_cp)
            
            if start_time is not None and end_time is not None:
                durations[f"{phase_name}_ms"] = round(end_time - start_time)
            else:
                durations[f"{phase_name}_ms"] = None
        
        durations["checkpoint_count"] = len(self._marks)
        return durations
    
    def report(
        self,
        log_func=None,
        write_to_file: bool = True,
        log_path: Optional[str] = None,
    ) -> None:
        """
        Output the profiling report.
        
        Args:
            log_func: Optional function to use for logging (e.g., logger.info)
            write_to_file: Whether to write detailed report to file
            log_path: Path for the report file (defaults to ~/.claude/startup-perf/)
        """
        if self._reported:
            return
        self._reported = True
        
        # Log to analytics (sampled sessions only)
        self._log_startup_perf()
        
        # Output detailed report if detailed profiling is enabled
        if self._detailed_profiling:
            report_text = self.get_report()
            
            if log_func:
                for line in report_text.split("\n"):
                    log_func(line)
            else:
                print(report_text)
            
            if write_to_file:
                if log_path is None:
                    home = Path.home()
                    session_id = os.environ.get("CLAUDE_SESSION_ID", datetime.now().strftime("%Y%m%d_%H%M%S"))
                    log_path = home / ".claude" / "startup-perf" / f"{session_id}.txt"
                
                log_path = Path(log_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_path.write_text(report_text, encoding="utf-8")
    
    def _log_startup_perf(self) -> None:
        """
        Log startup performance phases to analytics.
        Only logs if this session was sampled at startup.
        """
        if not self._sampled or not self._marks:
            return
        
        # This would integrate with an analytics service
        # For now, just return the metrics
        return self.get_phase_durations()
    
    def reset(self) -> None:
        """Reset all profiling state."""
        self._marks = []
        self._memory_snapshots = []
        self._reported = False


# Global profiler instance
_profiler: Optional[StartupProfiler] = None


def get_profiler() -> StartupProfiler:
    """Get the global profiler instance, creating if necessary."""
    global _profiler
    if _profiler is None:
        _profiler = StartupProfiler()
    return _profiler


def profile_checkpoint(name: str) -> None:
    """Convenience function to record a checkpoint."""
    get_profiler().checkpoint(name)


def profile_report() -> None:
    """Convenience function to output the profiling report."""
    get_profiler().report()


def is_detailed_profiling_enabled() -> bool:
    """Check if detailed profiling is enabled."""
    return get_profiler().is_detailed_profiling_enabled()
