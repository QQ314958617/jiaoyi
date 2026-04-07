"""
Coordinator - Multi-Agent Orchestration System

A coordinator agent that orchestrates work across multiple worker agents.
Based on Claude Code's coordinatorMode.ts (369 lines).

Key concepts:
- Coordinator vs Workers: One coordinator orchestrates, multiple workers execute
- Task notification XML: Inter-agent result format
- Parallel spawning: Fan out research, serialize implementation
- Continue vs Spawn: Reuse context vs fresh start
- Phase workflow: Research → Synthesis → Implementation → Verification
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from xml.etree import ElementTree as ET


class AgentRole(Enum):
    COORDINATOR = "coordinator"
    WORKER = "worker"


class TaskStatus(Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"
    RUNNING = "running"


class TaskPhase(Enum):
    RESEARCH = "research"
    SYNTHESIS = "synthesis"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"


# ---------------------------------------------------------------------------
# Task Notification XML parsing
# ---------------------------------------------------------------------------

TASK_NOTIFICATION_PATTERN = re.compile(
    r"<task-notification>\s*"
    r"<task-id>([^<]*)</task-id>\s*"
    r"<status>([^<]*)</status>\s*"
    r"<summary>([^<]*)</summary>\s*"
    r"(?:<result>([^<]*)</result>\s*)?"
    r"(?:<usage>\s*"
    r"<total_tokens>([^<]*)</total_tokens>\s*"
    r"<tool_uses>([^<]*)</tool_uses>\s*"
    r"<duration_ms>([^<]*)</duration_ms>\s*"
    r"</usage>\s*)?"
    r"</task-notification>",
    re.DOTALL,
)


@dataclass
class TaskNotification:
    """Parsed result from a worker agent."""
    task_id: str
    status: TaskStatus
    summary: str
    result: str | None = None
    total_tokens: int | None = None
    tool_uses: int | None = None
    duration_ms: int | None = None

    @classmethod
    def parse(cls, text: str) -> TaskNotification | None:
        """Parse a task notification XML block from worker result text."""
        match = TASK_NOTIFICATION_PATTERN.search(text)
        if not match:
            return None
        task_id, status_str, summary, result, tokens, tool_uses, duration = match.groups()
        try:
            status = TaskStatus(status_str)
        except ValueError:
            status = TaskStatus.RUNNING
        return cls(
            task_id=task_id,
            status=status,
            summary=summary,
            result=result,
            total_tokens=int(tokens) if tokens else None,
            tool_uses=int(tool_uses) if tool_uses else None,
            duration_ms=int(duration) if duration else None,
        )


# ---------------------------------------------------------------------------
# Worker Agent
# ---------------------------------------------------------------------------

@dataclass
class WorkerAgent:
    """A worker agent that executes tasks autonomously."""
    agent_id: str
    description: str
    role: AgentRole = AgentRole.WORKER
    status: TaskStatus = TaskStatus.RUNNING
    result: str | None = None
    spawned_at: float = field(default_factory=time.time)
    context_files: list[str] = field(default_factory=list)  # Files loaded in context


@dataclass
class WorkerPrompt:
    """Specification for spawning a worker."""
    description: str
    prompt: str
    role: AgentRole = AgentRole.WORKER
    purpose: str | None = None  # e.g. "research for PR description", "quick check before merge"

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "prompt": self.prompt,
            "role": self.role.value,
            **({"purpose": self.purpose} if self.purpose else {}),
        }


# ---------------------------------------------------------------------------
# Coordinator Decision Logic
# ---------------------------------------------------------------------------

class SpawnDecision(Enum):
    CONTINUE = "continue"      # Use SendMessage to continue existing worker
    SPAWN = "spawn"            # Spawn fresh worker
    STOP_AND_SPAWN = "stop_and_spawn"  # Stop wrong-direction worker, spawn new


@dataclass
class SpawnDecisionResult:
    decision: SpawnDecision
    reason: str
    existing_worker_id: str | None = None


def decide_continue_vs_spawn(
    research_worker_id: str | None,
    research_phase: TaskPhase,
    implementation_files: list[str],
    worker_context_files: list[str],
    error_context: str | None = None,
) -> SpawnDecisionResult:
    """
    Decide whether to continue an existing worker or spawn a fresh one.

    Decision matrix:
    | Situation                                        | Decision       |
    |--------------------------------------------------|----------------|
    | Research explored same files for implementation  | CONTINUE       |
    | Broad research, narrow implementation             | SPAWN          |
    | Worker failed, correcting                        | CONTINUE       |
    | Verifying code a different worker wrote           | SPAWN          |
    | First attempt used wrong approach                 | STOP_AND_SPAWN |
    | Unrelated task                                   | SPAWN          |
    """
    if research_worker_id is None:
        return SpawnDecisionResult(SpawnDecision.SPAWN, "No existing worker")

    if error_context:
        return SpawnDecisionResult(
            SpawnDecision.CONTINUE,
            f"Worker failed with error context: {error_context[:50]}...",
            research_worker_id,
        )

    # Check context overlap
    overlap = set(implementation_files) & set(worker_context_files)
    overlap_ratio = len(overlap) / max(len(implementation_files), 1)

    if research_phase == TaskPhase.RESEARCH:
        if overlap_ratio > 0.6:
            return SpawnDecisionResult(
                SpawnDecision.CONTINUE,
                f"High context overlap ({overlap_ratio:.0%}), continuing worker {research_worker_id}",
                research_worker_id,
            )
        else:
            return SpawnDecisionResult(
                SpawnDecision.SPAWN,
                f"Low context overlap ({overlap_ratio:.0%}), spawning fresh worker",
            )

    if research_phase == TaskPhase.VERIFICATION:
        return SpawnDecisionResult(
            SpawnDecision.SPAWN,
            "Verification needs fresh eyes, spawning independent verifier",
        )

    return SpawnDecisionResult(SpawnDecision.SPAWN, "Default to spawn for implementation")


# ---------------------------------------------------------------------------
# Coordinator System Prompt
# ---------------------------------------------------------------------------

def build_coordinator_system_prompt(
    worker_capabilities: str,
    mcp_servers: list[str] | None = None,
    scratchpad_dir: str | None = None,
    scratchpad_enabled: bool = False,
) -> str:
    """
    Build the system prompt for a coordinator agent.

    Args:
        worker_capabilities: Description of tools available to workers
        mcp_servers: List of connected MCP server names
        scratchpad_dir: Directory for cross-worker knowledge sharing
        scratchpad_enabled: Whether scratchpad feature is enabled
    """
    prompt = """You are a coordinator. Your job is to:
- Help the user achieve their goal
- Direct workers to research, implement and verify code changes
- Synthesize results and communicate with the user
- Answer questions directly when possible — don't delegate work you can handle

Every message you send is to the user. Worker results are internal signals — 
never thank or acknowledge them. Summarize new information for the user as it arrives.

## Worker Tools

Workers can be spawned with the Agent tool, continued with SendMessage tool,
and stopped with TaskStop tool.

## Worker Results

Results arrive as task notification blocks in this format:

```xml
<task-notification>
<task-id>{agent_id}</task-id>
<status>completed|failed|killed</status>
<summary>{human-readable summary}</summary>
<result>{worker's final response}</result>
<usage>
  <total_tokens>N</total_tokens>
  <tool_uses>N</tool_uses>
  <duration_ms>N</duration_ms>
</usage>
</task-notification>
```

## Phase Workflow

Most tasks follow these phases:

1. **Research** (Workers, parallel) — Investigate codebase, find files, understand problem
2. **Synthesis** (You) — Read findings, craft implementation specs
3. **Implementation** (Workers) — Make targeted changes per spec
4. **Verification** (Workers) — Prove the code works

## Parallelism

**Launch independent workers concurrently.** Don't serialize work that can run simultaneously.
- Read-only tasks → parallel freely
- Write-heavy tasks → one at a time per file set
- Verification can run alongside implementation on different areas

## Verification Standards

Verification means proving the code works, not confirming it exists.
- Run tests with the feature enabled
- Investigate errors, don't dismiss as "unrelated"
- Test edge cases and error paths

## Worker Prompting

Workers can't see your conversation. Every prompt must be self-contained.
Always synthesize findings before directing follow-up work.
Include specific file paths, line numbers, and exactly what to change.

**Good spec example:**
"Fix the null pointer in src/auth/validate.ts:42. The user field is undefined
when sessions expire. Add a null check before user.id access — if null,
return 401 with 'Session expired'. Run tests and commit."

**Bad spec:**
"Fix the bug we discussed" — no context, workers can't see your conversation
"Based on your findings, implement the fix" — lazy delegation

## Continue vs Spawn

After research completes, decide based on context overlap:
- Same files needed → CONTINUE (worker has context + clear plan)
- Broad research, narrow implementation → SPAWN fresh
- Worker already has error context → CONTINUE
- Verifying another worker's code → SPAWN fresh
- Wrong approach used → STOP and SPAWN fresh
"""
    if mcp_servers:
        prompt += f"\n\nMCP servers available to workers: {', '.join(mcp_servers)}"
    if scratchpad_dir and scratchpad_enabled:
        prompt += f"\n\nScratchpad directory: {scratchpad_dir}\nWorkers can use this for cross-worker knowledge sharing."

    return prompt


# ---------------------------------------------------------------------------
# Coordinator Context
# ---------------------------------------------------------------------------

@dataclass
class CoordinatorContext:
    """Runtime context for a coordinator session."""
    # Active workers
    workers: dict[str, WorkerAgent] = field(default_factory=dict)

    # Completed results
    completed_tasks: dict[str, TaskNotification] = field(default_factory=dict)

    # Phase tracking
    current_phase: TaskPhase = TaskPhase.RESEARCH

    # Feature flags
    coordinator_mode: bool = False
    simple_mode: bool = False

    # Config
    mcp_servers: list[str] = field(default_factory=list)
    scratchpad_dir: str | None = None
    scratchpad_enabled: bool = False

    def add_worker(self, worker: WorkerAgent) -> None:
        self.workers[worker.agent_id] = worker

    def complete_task(self, notification: TaskNotification) -> None:
        self.completed_tasks[notification.task_id] = notification
        if notification.task_id in self.workers:
            self.workers[notification.task_id].status = notification.status
            self.workers[notification.task_id].result = notification.result

    def get_running_workers(self) -> list[WorkerAgent]:
        return [w for w in self.workers.values() if w.status == TaskStatus.RUNNING]

    def stop_worker(self, task_id: str) -> bool:
        if task_id in self.workers:
            self.workers[task_id].status = TaskStatus.KILLED
            return True
        return False


# ---------------------------------------------------------------------------
# Coordinator - Main Orchestration Class
# ---------------------------------------------------------------------------

class Coordinator:
    """
    Multi-agent coordinator that orchestrates work across workers.

    Usage:
        coord = Coordinator(worker_capabilities="Workers have Bash, Read, Edit tools")
        coord.spawn_worker("Investigate auth bug", "Look into src/auth/ for null pointers...")
        # ... receive results ...
        coord.synthesize_and_continue(worker_id, "Now fix the null pointer in src/auth/validate.ts:42")
    """

    def __init__(
        self,
        worker_capabilities: str,
        mcp_servers: list[str] | None = None,
        scratchpad_dir: str | None = None,
        simple: bool = False,
    ):
        self.ctx = CoordinatorContext(
            coordinator_mode=True,
            simple_mode=simple,
            mcp_servers=mcp_servers or [],
            scratchpad_dir=scratchpad_dir,
        )
        self._worker_counter = 0
        self._worker_capabilities = worker_capabilities

    def generate_id(self) -> str:
        self._worker_counter += 1
        return f"agent-{self._worker_counter:03d}"

    def spawn_worker(
        self,
        description: str,
        prompt: str,
        purpose: str | None = None,
    ) -> str:
        """
        Spawn a new worker agent.

        Returns the worker agent_id for use with continue/stop.
        """
        agent_id = self.generate_id()
        worker = WorkerAgent(
            agent_id=agent_id,
            description=description,
            role=AgentRole.WORKER,
        )
        self.ctx.add_worker(worker)
        return agent_id

    def build_worker_prompt(self, spec: str, purpose: str | None = None) -> str:
        """Build a complete worker prompt with optional purpose statement."""
        if purpose:
            return f"[Purpose: {purpose}]\n\n{spec}"
        return spec

    def parse_results(self, text: str) -> list[TaskNotification]:
        """Extract all task notifications from a text block."""
        results = []
        for match in TASK_NOTIFICATION_PATTERN.finditer(text):
            status_str = match.group(2)
            try:
                status = TaskStatus(status_str)
            except ValueError:
                status = TaskStatus.RUNNING
            results.append(TaskNotification(
                task_id=match.group(1),
                status=status,
                summary=match.group(3),
                result=match.group(4),
                total_tokens=int(match.group(5)) if match.group(5) else None,
                tool_uses=int(match.group(6)) if match.group(6) else None,
                duration_ms=int(match.group(7)) if match.group(7) else None,
            ))
        return results

    def decide_spawn(
        self,
        worker_id: str | None,
        implementation_files: list[str],
        worker_context_files: list[str],
        error_context: str | None = None,
    ) -> SpawnDecisionResult:
        """Make a continue vs spawn decision."""
        return decide_continue_vs_spawn(
            research_worker_id=worker_id,
            research_phase=self.ctx.current_phase,
            implementation_files=implementation_files,
            worker_context_files=worker_context_files,
            error_context=error_context,
        )

    def report_status(self) -> str:
        """Generate a human-readable status report."""
        running = self.ctx.get_running_workers()
        completed = list(self.ctx.completed_tasks.values())

        lines = [
            f"Coordinator Status",
            f"  Phase: {self.ctx.current_phase.value}",
            f"  Running workers: {len(running)}",
            f"  Completed tasks: {len(completed)}",
        ]

        if running:
            lines.append("  Active workers:")
            for w in running:
                age = time.time() - w.spawned_at
                lines.append(f"    - {w.agent_id}: {w.description} ({age:.0f}s ago)")

        if completed:
            lines.append("  Completed:")
            for t in completed[-3:]:  # Last 3
                lines.append(f"    - {t.task_id}: {t.status.value} — {t.summary[:60]}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience factories for specific strategies
# ---------------------------------------------------------------------------

def parallel_research(
    coordinator: Coordinator,
    tasks: list[tuple[str, str, str]],  # (description, prompt, purpose)
) -> list[str]:
    """
    Spawn multiple research workers in parallel.

    Args:
        coordinator: The coordinator instance
        tasks: List of (description, prompt, purpose) tuples

    Returns:
        List of worker agent_ids
    """
    return [
        coordinator.spawn_worker(desc, coordinator.build_worker_prompt(prompt, purpose))
        for desc, prompt, purpose in tasks
    ]


def synthesize_spec(
    findings: str,
    file_path: str,
    line_ref: str | None = None,
    action: str = "Fix",
) -> str:
    """
    Synthesize research findings into an implementation spec.

    Args:
        findings: Raw research findings from worker
        file_path: Target file to modify
        line_ref: Specific line or line range (e.g. "line 42" or "lines 42-45")
        action: What to do (e.g. "Fix", "Refactor", "Add")

    Returns:
        A complete, self-contained spec string
    """
    spec = f"{action} in {file_path}"
    if line_ref:
        spec += f":{line_ref}"
    spec += f"\n\n{findings}\n\nRun tests and commit your changes. Report the commit hash."
    return spec


# ---------------------------------------------------------------------------
# Simple coordinator mode detection
# ---------------------------------------------------------------------------

def is_coordinator_mode_enabled() -> bool:
    """Check if coordinator mode is enabled via environment variable."""
    return os.environ.get("CLAUDE_CODE_COORDINATOR_MODE", "0") in ("1", "true", "yes")


def enable_coordinator_mode() -> None:
    """Enable coordinator mode."""
    os.environ["CLAUDE_CODE_COORDINATOR_MODE"] = "1"


def disable_coordinator_mode() -> None:
    """Disable coordinator mode."""
    os.environ.pop("CLAUDE_CODE_COORDINATOR_MODE", None)


if __name__ == "__main__":
    # Demo / smoke test
    coord = Coordinator(
        worker_capabilities="Workers have Bash, Read, Edit tools and MCP tools",
        mcp_servers=["filesystem", "github"],
        simple=False,
    )

    # Spawn parallel research workers
    worker_ids = parallel_research(
        coord,
        [
            ("Investigate auth bug", "Look into src/auth/ for null pointer issues around session handling. Report file paths and line numbers.", "inform PR description"),
            ("Research token storage", "Find where tokens are stored and validated in src/auth/. Report the key functions involved.", "plan implementation"),
        ]
    )
    print(f"Spawned workers: {worker_ids}")
    print(coord.report_status())

    # Test spec synthesis
    spec = synthesize_spec(
        findings="Found null pointer at src/auth/validate.ts:42. The user field is undefined when Session.expired=true but token is still cached.",
        file_path="src/auth/validate.ts",
        line_ref="42",
        action="Fix null pointer",
    )
    print("\nSynthesized spec:")
    print(spec)

    # Test task notification parsing
    sample = """
    Checked the codebase.
    <task-notification>
    <task-id>agent-001</task-id>
    <status>completed</status>
    <summary>Agent "Investigate auth bug" completed</summary>
    <result>Found null pointer in src/auth/validate.ts:42</result>
    <usage>
      <total_tokens>5000</total_tokens>
      <tool_uses>42</tool_uses>
      <duration_ms>15000</duration_ms>
    </usage>
    </task-notification>
    """
    parsed = coord.parse_results(sample)
    print(f"\nParsed notifications: {len(parsed)}")
    if parsed:
        n = parsed[0]
        print(f"  ID: {n.task_id}, Status: {n.status.value}, Tokens: {n.total_tokens}")

    print("\n✅ coordinator.py OK")
