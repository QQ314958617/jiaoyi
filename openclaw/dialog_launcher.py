"""
Dialog Launcher System - Ported from Claude Code's src/dialogLaunchers.tsx

Thin launchers for one-off dialog sites. Each launcher dynamically imports
its component and wires a done callback identically to the original call site.

Python adaptation for modal/overlay dialog management in Flask/CLI contexts.

Key patterns:
- Dynamic import pattern for lazy loading
- show_setup_dialog vs render_and_run separation
- Promise-based async dialog completion
- Setup wizard flow with error handling
"""

from __future__ import annotations

import asyncio
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Optional,
    Protocol,
    TypeVar,
)
from typing_extensions import ParamSpec

P = ParamSpec('P')
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)


# ============================================================================
# Dialog Result Types
# ============================================================================

class DialogResult(Enum):
    """Standard dialog result types."""
    OK = 'ok'
    CANCEL = 'cancel'
    YES = 'yes'
    NO = 'no'
    CLOSE = 'close'
    KEEP = 'keep'
    MERGE = 'merge'
    REPLACE = 'replace'


# ============================================================================
# Dialog Component Protocol (adapted from React components)
# ============================================================================

class DialogComponent(ABC, Generic[T]):
    """Abstract base for dialog components."""
    
    @abstractmethod
    async def render(self) -> str:
        """Render the dialog content (returns HTML/text)."""
        pass
    
    @abstractmethod
    async def handle_result(self, result: T) -> None:
        """Handle the dialog result."""
        pass


# ============================================================================
# Dialog Context
# ============================================================================

@dataclass
class DialogContext:
    """Context for a running dialog."""
    dialog_id: str
    dialog_type: str
    started_at: float = field(default_factory=lambda: __import__('time').time())
    completed: bool = False
    result: Any = None
    error: Optional[Exception] = None


class DialogState(Enum):
    """Dialog lifecycle states."""
    PENDING = 'pending'
    RENDERING = 'rendering'
    AWAITING_INPUT = 'awaiting_input'
    COMPLETING = 'completing'
    DONE = 'done'
    ERROR = 'error'


# ============================================================================
# Show Setup Dialog Pattern
# ============================================================================

class SetupDialogClosed(Exception):
    """Exception raised when a setup dialog is closed/cancelled."""
    pass


class SetupDialogError(Exception):
    """Exception raised when a setup dialog encounters an error."""
    pass


class DialogLauncher:
    """
    Manager for launching and tracking dialogs.
    
    Adapted from the React-based dialog launcher pattern.
    """
    
    def __init__(self):
        self._active_dialogs: dict[str, DialogContext] = {}
        self._dialog_counter = 0
    
    def _generate_dialog_id(self) -> str:
        """Generate unique dialog ID."""
        self._dialog_counter += 1
        import uuid
        return f"dialog_{uuid.uuid4().hex[:8]}_{self._dialog_counter}"
    
    async def show_setup_dialog(
        self,
        root: Any,
        done_callback: Callable[[Any], None],
        component_loader: Callable[[], Awaitable[Any]],
    ) -> Any:
        """
        Show a setup dialog with a done callback.
        
        This follows the pattern from dialogLaunchers.tsx where:
        1. Component is dynamically imported
        2. Dialog is rendered with a done callback
        3. Result is passed to the callback
        
        Args:
            root: Root context (e.g., Ink root, Flask app context)
            done_callback: Called with result when dialog completes
            component_loader: Async function that loads the dialog component
            
        Returns:
            The dialog result
            
        Raises:
            SetupDialogClosed: If dialog is cancelled/closed
            SetupDialogError: If dialog encounters an error
        """
        dialog_id = self._generate_dialog_id()
        context = DialogContext(dialog_id=dialog_id, dialog_type='setup')
        self._active_dialogs[dialog_id] = context
        
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        
        def wrapped_done(result: Any) -> None:
            context.completed = True
            context.result = result
            if not future.done():
                future.set_result(result)
            done_callback(result)
        
        try:
            # Load component dynamically
            context.state = DialogState.RENDERING
            component = await component_loader()
            
            context.state = DialogState.AWAITING_INPUT
            
            # For synchronous done callbacks, wrap in async
            if asyncio.iscoroutinefunction(component.handle_result):
                await component.handle_result(wrapped_done)
            else:
                component.handle_result(wrapped_done)
            
            # Wait for completion
            return await future
            
        except Exception as e:
            context.error = e
            context.state = DialogState.ERROR
            raise SetupDialogError(str(e)) from e
        finally:
            self._active_dialogs.pop(dialog_id, None)
    
    def get_active_dialogs(self) -> list[DialogContext]:
        """Get all currently active dialogs."""
        return list(self._active_dialogs.values())


# Global dialog launcher
_dialog_launcher: Optional[DialogLauncher] = None


def get_dialog_launcher() -> DialogLauncher:
    """Get the global dialog launcher instance."""
    global _dialog_launcher
    if _dialog_launcher is None:
        _dialog_launcher = DialogLauncher()
    return _dialog_launcher


# ============================================================================
# Specific Dialog Launchers (ported from dialogLaunchers.tsx)
# ============================================================================

async def launch_snapshot_update_dialog(
    root: Any,
    agent_type: str,
    scope: str,
    snapshot_timestamp: str,
) -> str:
    """
    Launch snapshot update dialog.
    
    Args:
        root: Root context
        agent_type: Type of agent
        scope: Memory scope
        snapshot_timestamp: Timestamp of snapshot
        
    Returns:
        'merge', 'keep', or 'replace'
    """
    # In Python context, this would be adapted for the UI framework
    # For now, provide the async pattern
    
    async def component_loader():
        # Placeholder - in real implementation, would load actual dialog
        class SnapshotUpdateDialog(DialogComponent[str]):
            async def render(self) -> str:
                return f"Snapshot update dialog for {agent_type} ({scope})"
            
            async def handle_result(self, done: Callable[[str], None]) -> None:
                # In real impl, this would render HTML and wait for user input
                done('keep')
        
        return SnapshotUpdateDialog()
    
    async def done_callback(result: str) -> None:
        pass  # Handle result
    
    return await get_dialog_launcher().show_setup_dialog(
        root, done_callback, component_loader
    )


async def launch_invalid_settings_dialog(
    root: Any,
    settings_errors: list[dict],
    on_exit: Callable[[], None],
) -> None:
    """
    Launch invalid settings dialog.
    
    Args:
        root: Root context
        settings_errors: List of validation errors
        on_exit: Called when user exits
    """
    async def component_loader():
        class InvalidSettingsDialog(DialogComponent[None]):
            async def render(self) -> str:
                errors_str = '\n'.join(
                    f"- {e.get('path', '')}: {e.get('message', '')}"
                    for e in settings_errors
                )
                return f"Invalid settings:\n{errors_str}"
            
            async def handle_result(self, done: Callable[[None], None]) -> None:
                done(None)
        
        return InvalidSettingsDialog()
    
    async def done_callback(result: None) -> None:
        pass
    
    return await get_dialog_launcher().show_setup_dialog(
        root, done_callback, component_loader
    )


async def launch_assistant_session_chooser(
    root: Any,
    sessions: list[dict],
) -> Optional[str]:
    """
    Launch assistant session chooser dialog.
    
    Args:
        root: Root context
        sessions: Available assistant sessions
        
    Returns:
        Selected session ID or None if cancelled
    """
    async def component_loader():
        class AssistantSessionChooser(DialogComponent[Optional[str]]):
            async def render(self) -> str:
                return f"Choose assistant session ({len(sessions)} available)"
            
            async def handle_result(self, done: Callable[[Optional[str]], None]) -> None:
                if sessions:
                    done(sessions[0].get('id'))
                else:
                    done(None)
        
        return AssistantSessionChooser()
    
    async def done_callback(result: Optional[str]) -> None:
        pass
    
    return await get_dialog_launcher().show_setup_dialog(
        root, done_callback, component_loader
    )


async def launch_assistant_install_wizard(
    root: Any,
    default_dir: str,
) -> Optional[str]:
    """
    Launch assistant install wizard.
    
    Args:
        root: Root context
        default_dir: Default installation directory
        
    Returns:
        Installed directory path or None on cancel
    """
    async def component_loader():
        class NewInstallWizard(DialogComponent[Optional[str]]):
            async def render(self) -> str:
                return f"Install assistant to {default_dir}"
            
            async def handle_result(
                self, done: Callable[[Optional[str]], None]
            ) -> None:
                done(default_dir)
        
        return NewInstallWizard()
    
    async def done_callback(result: Optional[str]) -> None:
        pass
    
    # Race between result and error
    async def error_callback(message: str) -> None:
        raise SetupDialogError(f"Installation failed: {message}")
    
    result_future = get_dialog_launcher().show_setup_dialog(
        root, done_callback, component_loader
    )
    error_future = asyncio.get_event_loop().create_future()
    
    try:
        return await asyncio.wait_for(result_future, timeout=None)
    except SetupDialogError:
        raise


async def launch_teleport_resume_wrapper(
    root: Any,
) -> Optional[dict]:
    """
    Launch teleport resume wrapper dialog.
    
    Args:
        root: Root context
        
    Returns:
        TeleportRemoteResponse or None if cancelled
    """
    async def component_loader():
        class TeleportResumeWrapper(DialogComponent[Optional[dict]]):
            async def render(self) -> str:
                return "Select session to resume"
            
            async def handle_result(
                self, done: Callable[[Optional[dict]], None]
            ) -> None:
                done(None)
        
        return TeleportResumeWrapper()
    
    async def done_callback(result: Optional[dict]) -> None:
        pass
    
    return await get_dialog_launcher().show_setup_dialog(
        root, done_callback, component_loader
    )


async def launch_teleport_repo_mismatch_dialog(
    root: Any,
    target_repo: str,
    initial_paths: list[str],
) -> Optional[str]:
    """
    Launch teleport repo mismatch dialog.
    
    Args:
        root: Root context
        target_repo: Target repository
        initial_paths: Initial paths to display
        
    Returns:
        Selected path or None if cancelled
    """
    async def component_loader():
        class TeleportRepoMismatchDialog(DialogComponent[Optional[str]]):
            async def render(self) -> str:
                return f"Select checkout for {target_repo}"
            
            async def handle_result(
                self, done: Callable[[Optional[str]], None]
            ) -> None:
                if initial_paths:
                    done(initial_paths[0])
                else:
                    done(None)
        
        return TeleportRepoMismatchDialog()
    
    async def done_callback(result: Optional[str]) -> None:
        pass
    
    return await get_dialog_launcher().show_setup_dialog(
        root, done_callback, component_loader
    )


async def launch_resume_chooser(
    root: Any,
    app_props: dict,
    worktree_paths_promise: Awaitable[list[str]],
    resume_props: dict,
) -> None:
    """
    Launch resume conversation chooser.
    
    This differs from show_setup_dialog - uses render_and_run pattern
    directly (not wrapped in showSetupDialog).
    
    Args:
        root: Root context
        app_props: App component props
        worktree_paths_promise: Promise of worktree paths
        resume_props: Resume conversation props
    """
    # Parallel loading of resources
    worktree_paths = await worktree_paths_promise
    
    # Merge worktree paths into resume props
    full_props = {**resume_props, 'worktreePaths': worktree_paths}
    
    # In Python/Flask context, this would render the resume UI
    # and wait for user to select a session
    pass


# ============================================================================
# Flask Integration Helpers
# ============================================================================

class FlaskDialogMixin:
    """
    Mixin for Flask routes to support dialog launching.
    
    Usage:
        class MyRoute(DialogMixin, MethodView):
            pass
    """
    
    dialog_launcher: DialogLauncher = field(default_factory=get_dialog_launcher)
    
    async def show_modal(
        self,
        template: str,
        result_type: type[T],
        on_submit: Callable[[T], None],
    ) -> str:
        """
        Show a modal dialog and wait for result.
        
        Args:
            template: Jinja2 template name
            result_type: Expected result type
            on_submit: Callback when user submits
            
        Returns:
            Rendered HTML
        """
        raise NotImplementedError
    
    def register_dialog_route(
        self,
        name: str,
        template: str,
        handler: Callable[[dict], Any],
    ) -> None:
        """
        Register a dialog route.
        
        Args:
            name: Dialog name
            template: Template to render
            handler: Handler function for dialog result
        """
        # In real implementation, would register Flask route
        pass


# ============================================================================
# CLI Integration Helpers
# ============================================================================

class CliDialogRunner:
    """
    Run dialogs in CLI context (non-interactive fallback).
    
    For scripted/headless environments where UI dialogs can't render.
    """
    
    def __init__(
        self,
        default_answers: Optional[dict[str, Any]] = None,
        auto_confirm: bool = False,
    ):
        """
        Initialize CLI dialog runner.
        
        Args:
            default_answers: Default answers for each dialog type
            auto_confirm: Auto-confirm all dialogs without prompting
        """
        self.default_answers = default_answers or {}
        self.auto_confirm = auto_confirm
    
    async def run_dialog(
        self,
        dialog_name: str,
        **kwargs,
    ) -> Any:
        """
        Run a dialog in CLI mode.
        
        In auto_confirm mode, uses default answers.
        Otherwise, raises error indicating dialog can't be shown.
        
        Args:
            dialog_name: Name of dialog to run
            **kwargs: Dialog-specific arguments
            
        Returns:
            Dialog result
        """
        if self.auto_confirm:
            return self.default_answers.get(dialog_name)
        
        raise SetupDialogClosed(
            f"Dialog '{dialog_name}' cannot be shown in headless mode. "
            "Use auto_confirm=True or provide default answers."
        )
