"""
RemoteIO - Bidirectional Streaming for SDK Mode

Ported from Claude Code's src/cli/remoteIO.ts

Provides:
- RemoteIO class: extends StructuredIO for SDK mode
- WebSocket/SSE transport support
- Session token refresh handling
- CCR v2 client integration
- Keep-alive ping mechanism
- Graceful cleanup

Key design patterns:
- Transport abstraction (WebSocket, SSE, etc.)
- Dynamic header refresh callback
- CCR v2 state reporting
- Graceful shutdown with cleanup registry
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Optional,
)
from urllib.parse import urlparse

# ============================================================================
# Transport Types
# ============================================================================

class TransportType(Enum):
    """Transport protocol types."""
    WEBSOCKET = 'websocket'
    SSE = 'sse'
    HTTP = 'http'
    STDIO = 'stdio'


@dataclass
class TransportConfig:
    """Configuration for a transport connection."""
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    reconnect: bool = True
    reconnect_delay: float = 1.0
    max_reconnect_delay: float = 60.0


# ============================================================================
# Base Transport Interface
# ============================================================================

class Transport(ABC):
    """
    Abstract base for transport implementations.
    
    Each transport handles a specific protocol (WebSocket, SSE, HTTP, etc.)
    for bidirectional communication with the remote session.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to remote endpoint."""
        pass
    
    @abstractmethod
    async def write(self, message: Dict[str, Any]) -> None:
        """Send a message to the remote endpoint."""
        pass
    
    @abstractmethod
    async def read(self) -> AsyncIterator[Dict[str, Any]]:
        """Read messages from the remote endpoint."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the connection."""
        pass
    
    @abstractmethod
    def set_on_data(self, callback: Callable[[str], None]) -> None:
        """Set callback for incoming data."""
        pass
    
    @abstractmethod
    def set_on_close(self, callback: Callable[[], None]) -> None:
        """Set callback for connection close."""
        pass


# ============================================================================
# Message Types (from StdoutMessage)
# ============================================================================

class MessageType(str, Enum):
    """Structured message types for SDK communication."""
    # Output messages
    TEXT = 'text'
    TOOL_USE = 'tool_use'
    TOOL_RESULT = 'tool_result'
    TOOL_ERROR = 'tool_error'
    CONTENT = 'content'
    EMPTY = 'empty'
    MARKER = 'marker'
    PARTIAL_MESSAGE = 'partial_message'
    PARTIAL_MESSAGE_END = 'partial_message_end'
    SUBSCRIPTION_UPDATE = 'subscription_update'
    
    # Control messages
    CONTROL_REQUEST = 'control_request'
    CONTROL_RESPONSE = 'control_response'
    KEEP_ALIVE = 'keep_alive'
    
    # Error messages
    ERROR = 'error'
    ABORT = 'abort'


@dataclass
class BaseMessage:
    """Base class for structured messages."""
    type: MessageType
    
    def to_dict(self) -> Dict[str, Any]:
        return {'type': self.type.value if isinstance(self.type, Enum) else self.type}
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class TextMessage(BaseMessage):
    """Text output message."""
    content: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d['content'] = self.content
        return d


@dataclass
class ToolUseMessage(BaseMessage):
    """Tool use message."""
    tool_use_id: str = ''
    tool_name: str = ''
    input: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'toolUseId': self.tool_use_id,
            'tool': self.tool_name,
            'input': self.input,
        })
        return d


@dataclass  
class ControlRequestMessage(BaseMessage):
    """Control request (permission, etc.)."""
    request_id: str = ''
    request_type: str = ''
    request_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            'requestId': self.request_id,
            'requestType': self.request_type,
            'requestData': self.request_data,
        })
        return d


@dataclass
class KeepAliveMessage(BaseMessage):
    """Keep-alive ping message."""
    
    @staticmethod
    def make() -> Dict[str, Any]:
        return {'type': 'keep_alive'}


# ============================================================================
# StructuredIO Base (headless mode output)
# ============================================================================

class StructuredIO:
    """
    Base class for structured output in headless/SDK mode.
    
    Handles:
    - Input stream reading
    - Message parsing (NDJSON)
    - Output formatting
    - Replay user messages mode
    """
    
    def __init__(
        self,
        input_stream: Optional[asyncio.StreamReader] = None,
        replay_user_messages: bool = False,
    ):
        self.input_stream = input_stream
        self.replay_user_messages = replay_user_messages
        self._reader_task: Optional[asyncio.Task] = None
        self._input_queue: asyncio.Queue = asyncio.Queue()
        self._closed = False
    
    async def start_reading(self) -> None:
        """Start reading from input stream."""
        if self._reader_task:
            return
        
        if self.input_stream:
            self._reader_task = asyncio.create_task(self._read_loop())
    
    async def _read_loop(self) -> None:
        """Read loop for input stream."""
        try:
            while not self._closed:
                if self.input_stream:
                    line = await self.input_stream.readline()
                    if not line:
                        break
                    
                    decoded = line.decode('utf-8').strip()
                    if decoded:
                        await self._input_queue.put(decoded)
                else:
                    await asyncio.sleep(0.1)
        except Exception as e:
            logging.error(f"StructuredIO read error: {e}")
        finally:
            self._closed = True
    
    async def read_input(self) -> AsyncGenerator[str, None]:
        """Read input messages as async generator."""
        await self.start_reading()
        
        while not self._closed:
            try:
                msg = await asyncio.wait_for(
                    self._input_queue.get(),
                    timeout=1.0
                )
                yield msg
            except asyncio.TimeoutError:
                continue
    
    def close(self) -> None:
        """Close the structured IO."""
        self._closed = True
        if self._reader_task:
            self._reader_task.cancel()
    
    def write_message(self, message: Dict[str, Any]) -> str:
        """
        Write a message as NDJSON string.
        
        Args:
            message: Message dict to serialize
            
        Returns:
            NDJSON formatted string
        """
        return json.dumps(message, ensure_ascii=False) + '\n'
    
    def flush_internal_events(self) -> Awaitable[None]:
        """Flush any pending internal events."""
        return asyncio.get_event_loop().create_future()


# ============================================================================
# WebSocket Transport
# ============================================================================

class WebSocketTransport(Transport):
    """
    WebSocket-based transport implementation.
    
    Uses asyncio websockets for bidirectional communication.
    """
    
    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        ping_interval: float = 30.0,
    ):
        self.url = url
        self.headers = headers or {}
        self.ping_interval = ping_interval
        
        self._ws: Optional[Any] = None  # websockets.WebSocketServerProtocol
        self._reader_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._on_data_callback: Optional[Callable[[str], None]] = None
        self._on_close_callback: Optional[Callable[[], None]] = None
        self._closed = False
        self._lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            import websockets
            
            parsed = urlparse(self.url)
            
            async with websockets.connect(
                self.url,
                extra_headers=self.headers,
                ping_interval=self.ping_interval,
            ) as ws:
                self._ws = ws
                
                # Start reader loop
                self._reader_task = asyncio.create_task(self._read_loop())
                
                # Start ping task
                self._ping_task = asyncio.create_task(self._ping_loop())
                
                # Wait until closed
                try:
                    await asyncio.get_event_loop().create_future()
                except asyncio.CancelledError:
                    pass
                    
        except Exception as e:
            logging.error(f"WebSocket connection failed: {e}")
            raise
    
    async def _read_loop(self) -> None:
        """Read messages from WebSocket."""
        try:
            async for message in self._ws:
                if self._on_data_callback and isinstance(message, str):
                    self._on_data_callback(message)
                elif self._on_data_callback and isinstance(message, bytes):
                    self._on_data_callback(message.decode('utf-8'))
        except Exception as e:
            if not self._closed:
                logging.error(f"WebSocket read error: {e}")
        finally:
            if self._on_close_callback:
                self._on_close_callback()
    
    async def _ping_loop(self) -> None:
        """Send periodic pings."""
        while not self._closed:
            await asyncio.sleep(self.ping_interval)
            if self._ws and not self._closed:
                try:
                    await self._ws.ping()
                except Exception:
                    break
    
    async def write(self, message: Dict[str, Any]) -> None:
        """Send message via WebSocket."""
        if self._ws:
            await self._ws.send(json.dumps(message, ensure_ascii=False))
    
    async def read(self) -> AsyncIterator[Dict[str, Any]]:
        """Read messages from WebSocket."""
        if self._ws:
            async for msg in self._ws:
                if isinstance(msg, str):
                    yield json.loads(msg)
                elif isinstance(msg, bytes):
                    yield json.loads(msg.decode('utf-8'))
    
    def close(self) -> None:
        """Close WebSocket connection."""
        self._closed = True
        if self._ping_task:
            self._ping_task.cancel()
        if self._reader_task:
            self._reader_task.cancel()
        if self._ws:
            asyncio.create_task(self._ws.close())
    
    def set_on_data(self, callback: Callable[[str], None]) -> None:
        """Set data callback."""
        self._on_data_callback = callback
    
    def set_on_close(self, callback: Callable[[], None]) -> None:
        """Set close callback."""
        self._on_close_callback = callback


# ============================================================================
# SSE Transport (Server-Sent Events)
# ============================================================================

class SSETransport(Transport):
    """
    Server-Sent Events transport implementation.
    
    Handles:
    - GET connection for receiving events
    - POST for sending messages
    - Automatic reconnection
    """
    
    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        session_id: str = '',
        refresh_headers: Optional[Callable[[], Dict[str, str]]] = None,
    ):
        self.url = url
        self.headers = headers or {}
        self.session_id = session_id
        self.refresh_headers = refresh_headers
        
        self._client: Optional[Any] = None  # aiohttp client session
        self._reader_task: Optional[asyncio.Task] = None
        self._on_data_callback: Optional[Callable[[str], None]] = None
        self._on_close_callback: Optional[Callable[[], None]] = None
        self._closed = False
        self._event_id = 0
    
    async def connect(self) -> None:
        """Establish SSE connection."""
        import aiohttp
        
        self._client = aiohttp.ClientSession()
        
        # Build SSE URL with session ID
        parsed = urlparse(self.url)
        sse_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            sse_url += f"?{parsed.query}&sessionId={self.session_id}"
        else:
            sse_url += f"?sessionId={self.session_id}"
        
        headers = {
            **self.headers,
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
        }
        
        try:
            async with self._client.get(sse_url, headers=headers) as resp:
                if resp.status != 200:
                    raise Exception(f"SSE connection failed: {resp.status}")
                
                self._reader_task = asyncio.create_task(self._read_loop(resp))
                
        except Exception as e:
            logging.error(f"SSE connection error: {e}")
            raise
    
    async def _read_loop(self, response: Any) -> None:
        """Read SSE events from response."""
        try:
            async for line in response.content:
                if self._closed:
                    break
                    
                line = line.decode('utf-8').strip()
                if not line:
                    continue
                
                if line.startswith('data:'):
                    data = line[5:].strip()
                    if data:
                        self._event_id += 1
                        if self._on_data_callback:
                            self._on_data_callback(data)
                        
                elif line.startswith('id:'):
                    try:
                        self._event_id = int(line[3:].strip())
                    except ValueError:
                        pass
                        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if not self._closed:
                logging.error(f"SSE read error: {e}")
        finally:
            if self._on_close_callback:
                self._on_close_callback()
    
    async def write(self, message: Dict[str, Any]) -> None:
        """Send message via POST request."""
        if self._client:
            # Refresh headers if callback provided
            headers = self.headers
            if self.refresh_headers:
                headers = self.refresh_headers()
            
            parsed = urlparse(self.url)
            post_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            await self._client.post(
                post_url,
                json=message,
                headers={**headers, 'Content-Type': 'application/json'},
            )
    
    async def read(self) -> AsyncIterator[Dict[str, Any]]:
        """SSE is receive-only, use write() for sending."""
        raise NotImplementedError("SSE transport does not support read()")
    
    def close(self) -> None:
        """Close SSE connection."""
        self._closed = True
        if self._reader_task:
            self._reader_task.cancel()
        if self._client:
            asyncio.create_task(self._client.close())
    
    def set_on_data(self, callback: Callable[[str], None]) -> None:
        """Set data callback."""
        self._on_data_callback = callback
    
    def set_on_close(self, callback: Callable[[], None]) -> None:
        """Set close callback."""
        self._on_close_callback = callback


# ============================================================================
# RemoteIO (main class extending StructuredIO)
# ============================================================================

class RemoteIO(StructuredIO):
    """
    Bidirectional streaming for SDK mode with session tracking.
    
    Extends StructuredIO to support:
    - Multiple transport types (WebSocket, SSE)
    - Session token refresh
    - CCR v2 client integration
    - Keep-alive pinging
    - Graceful cleanup
    
    This is the main entry point for remote SDK sessions.
    """
    
    def __init__(
        self,
        stream_url: str,
        initial_prompt: Optional[AsyncIterator[str]] = None,
        replay_user_messages: bool = False,
        session_id: str = '',
        session_token: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        transport_type: Optional[TransportType] = None,
    ):
        super().__init__(replay_user_messages=replay_user_messages)
        
        self.url = stream_url
        self.session_id = session_id
        self.session_token = session_token
        self.initial_headers = headers or {}
        self.transport_type = transport_type or self._detect_transport(stream_url)
        
        # Internal state
        self._input_stream_writer: Optional[asyncio.StreamWriter] = None
        self._transport: Optional[Transport] = None
        self._ccr_client: Optional[CCRClient] = None
        self._keep_alive_timer: Optional[asyncio.TimerHandle] = None
        self._keep_alive_interval_ms: int = 120_000  # 120s default
        self._is_bridge: bool = False
        self._is_debug: bool = False
        
        # Cleanup registry
        self._cleanup_callbacks: list[Callable] = []
        
        # If initial prompt provided, set up writer
        if initial_prompt:
            asyncio.create_task(self._write_initial_prompt(initial_prompt))
    
    def _detect_transport(self, url: str) -> TransportType:
        """Detect transport type from URL scheme."""
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        
        if scheme == 'wss' or scheme == 'ws':
            return TransportType.WEBSOCKET
        elif scheme == 'https' or scheme == 'http':
            return TransportType.SSE  # Default HTTP to SSE
        elif scheme == 'stdio':
            return TransportType.STDIO
        else:
            return TransportType.SSE  # Default
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers with session token."""
        headers = {
            **self.initial_headers,
        }
        
        if self.session_token:
            headers['Authorization'] = f'Bearer {self.session_token}'
        
        # Add environment runner version if available
        import os
        er_version = os.environ.get('CLAUDE_CODE_ENVIRONMENT_RUNNER_VERSION')
        if er_version:
            headers['x-environment-runner-version'] = er_version
        
        return headers
    
    def _refresh_headers(self) -> Dict[str, str]:
        """Refresh headers callback for reconnection."""
        # In real impl, would re-read session token from env/file
        return self._build_headers()
    
    async def connect(self) -> None:
        """Establish transport connection."""
        headers = self._build_headers()
        
        # Get appropriate transport
        self._transport = self._get_transport(headers)
        
        # Set up data callback
        if self._transport:
            self._transport.set_on_data(self._handle_data)
            self._transport.set_on_close(self._handle_close)
        
        # Connect
        if self._transport:
            await self._transport.connect()
        
        # Start CCR v2 client if enabled
        import os
        if os.environ.get('CLAUDE_CODE_USE_CCR_V2'):
            await self._init_ccr_v2()
        
        # Start keep-alive if bridge mode
        self._is_bridge = os.environ.get('CLAUDE_CODE_ENVIRONMENT_KIND') == 'bridge'
        if self._is_bridge and self._keep_alive_interval_ms > 0:
            self._start_keep_alive()
        
        # Register cleanup
        self._register_cleanup()
    
    def _get_transport(self, headers: Dict[str, str]) -> Transport:
        """Get transport instance for URL."""
        if self.transport_type == TransportType.WEBSOCKET:
            return WebSocketTransport(
                url=self.url,
                headers=headers,
            )
        elif self.transport_type == TransportType.SSE:
            return SSETransport(
                url=self.url,
                headers=headers,
                session_id=self.session_id,
                refresh_headers=self._refresh_headers,
            )
        else:
            raise ValueError(f"Unsupported transport type: {self.transport_type}")
    
    def _handle_data(self, data: str) -> None:
        """Handle incoming data."""
        # Write to input stream for StructuredIO
        if self._input_stream_writer:
            self._input_stream_writer.write(data.encode('utf-8'))
        
        # Echo to stdout in bridge debug mode
        if self._is_bridge and self._is_debug:
            import sys
            sys.stdout.write(data)
            sys.stdout.flush()
    
    def _handle_close(self) -> None:
        """Handle connection close."""
        self.close()
    
    async def _init_ccr_v2(self) -> None:
        """Initialize CCR v2 client for state reporting."""
        self._ccr_client = CCRClient(
            transport=self._transport,
            url=self.url,
        )
        
        try:
            await self._ccr_client.initialize()
        except Exception as e:
            logging.error(f"CCR v2 initialization failed: {e}")
    
    def _start_keep_alive(self) -> None:
        """Start keep-alive ping timer."""
        async def send_ping():
            try:
                await self.write(KeepAliveMessage.make())
            except Exception as e:
                logging.debug(f"Keep-alive write failed: {e}")
        
        loop = asyncio.get_event_loop()
        self._keep_alive_timer = loop.call_later(
            self._keep_alive_interval_ms / 1000,
            lambda: asyncio.create_task(send_ping())
        )
    
    def _register_cleanup(self) -> None:
        """Register cleanup callback."""
        # In real impl, would register with cleanup registry
        self._cleanup_callbacks.append(self._do_cleanup)
    
    async def _write_initial_prompt(
        self,
        prompt: AsyncIterator[str],
    ) -> None:
        """Write initial prompt to input stream."""
        if self._input_stream_writer is None:
            # Create pipe for input
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            await asyncio.get_event_loop().create_server(
                lambda: protocol,
                host=None,
                port=None,
            )
            self._input_stream_writer = asyncio.StreamWriter(
                asyncio.transports.WriteTransport,
                protocol,
                None,
                asyncio.get_event_loop(),
            )
        
        async for chunk in prompt:
            # Strip trailing newline to avoid double-newline issues
            cleaned = chunk.rstrip('\n')
            self._input_stream_writer.write(f"{cleaned}\n".encode('utf-8'))
    
    async def write(self, message: Dict[str, Any]) -> None:
        """Send output message to remote endpoint."""
        if self._ccr_client:
            await self._ccr_client.write_event(message)
        elif self._transport:
            await self._transport.write(message)
        
        # Echo to stdout in bridge mode for control requests
        if self._is_bridge:
            msg_type = message.get('type')
            if msg_type == 'control_request' or self._is_debug:
                import sys
                ndjson = json.dumps(message, ensure_ascii=False) + '\n'
                sys.stdout.write(ndjson)
                sys.stdout.flush()
    
    def close(self) -> None:
        """Gracefully close connection."""
        # Stop keep-alive
        if self._keep_alive_timer:
            self._keep_alive_timer.cancel()
            self._keep_alive_timer = None
        
        # Close transport
        if self._transport:
            self._transport.close()
            self._transport = None
        
        # Close CCR client
        if self._ccr_client:
            self._ccr_client.close()
            self._ccr_client = None
        
        # Close input stream
        if self._input_stream_writer:
            self._input_stream_writer.close()
            self._input_stream_writer = None
        
        # Run cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception:
                pass
    
    async def _do_cleanup(self) -> None:
        """Internal cleanup."""
        self.close()


# ============================================================================
# CCR Client (CCR v2 State Reporting)
# ============================================================================

@dataclass
class CCRClient:
    """
    Client for CCR v2 protocol (bridge state reporting).
    
    Handles:
    - Heartbeats
    - Epoch tracking
    - State reporting
    - Event writing
    - Internal event persistence
    """
    
    transport: Optional[Transport]
    url: str
    
    # State
    _initialized: bool = False
    _closed: bool = False
    _pending_events: int = 0
    
    # Callbacks for internal events
    _event_reader: Optional[Callable[[], Awaitable[list[dict]]]] = None
    _subagent_event_reader: Optional[Callable[[], Awaitable[list[dict]]]] = None
    _lifecycle_listener: Optional[Callable[[str, str], None]] = None
    
    async def initialize(self) -> None:
        """Initialize CCR v2 connection."""
        self._initialized = True
    
    async def write_event(self, message: Dict[str, Any]) -> None:
        """Write an event to CCR."""
        if self.transport and not self._closed:
            await self.transport.write(message)
        self._pending_events += 1
    
    async def write_internal_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write an internal event (transcript)."""
        event = {
            'type': 'internal_event',
            'eventType': event_type,
            'payload': payload,
            **(options or {}),
        }
        await self.write_event(event)
    
    async def read_internal_events(self) -> list[dict]:
        """Read internal events for session resume."""
        if self._event_reader:
            return await self._event_reader()
        return []
    
    async def read_subagent_internal_events(self) -> list[dict]:
        """Read subagent internal events."""
        if self._subagent_event_reader:
            return await self._subagent_event_reader()
        return []
    
    def report_delivery(self, uuid: str, state: str) -> None:
        """Report command lifecycle state."""
        if self._lifecycle_listener:
            self._lifecycle_listener(uuid, state)
    
    def report_state(self, state: str, details: Optional[Dict] = None) -> None:
        """Report session state change."""
        pass  # Would send to CCR
    
    def report_metadata(self, metadata: Dict[str, Any]) -> None:
        """Report session metadata."""
        pass  # Would send to CCR
    
    @property
    def internal_events_pending(self) -> int:
        """Number of internal events pending flush."""
        return self._pending_events
    
    async def flush_internal_events(self) -> None:
        """Flush pending internal events."""
        self._pending_events = 0
    
    def close(self) -> None:
        """Close CCR client."""
        self._closed = True
        self._initialized = False


# ============================================================================
# Factory Functions
# ============================================================================

def get_transport_for_url(
    url: str,
    headers: Dict[str, str],
    session_id: str,
    refresh_headers: Optional[Callable[[], Dict[str, str]]] = None,
) -> Transport:
    """
    Get appropriate transport for a given URL.
    
    Args:
        url: Connection URL
        headers: Request headers
        session_id: Session identifier
        refresh_headers: Callback to refresh headers
        
    Returns:
        Transport instance
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    
    if scheme in ('wss', 'ws'):
        return WebSocketTransport(url=url, headers=headers)
    elif scheme in ('https', 'http'):
        return SSETransport(
            url=url,
            headers=headers,
            session_id=session_id,
            refresh_headers=refresh_headers,
        )
    else:
        raise ValueError(f"Unknown URL scheme: {scheme}")


# ============================================================================
# Cleanup Registry Integration
# ============================================================================

class CleanupRegistry:
    """
    Registry for cleanup callbacks.
    
    Ensures proper cleanup order on shutdown.
    """
    
    def __init__(self):
        self._callbacks: list[Callable] = []
        self._registered = False
    
    def register(self, callback: Callable) -> None:
        """Register a cleanup callback."""
        self._callbacks.append(callback)
        if not self._registered:
            self._do_registration()
    
    def _do_registration(self) -> None:
        """Register with system cleanup."""
        # In real impl, would register with atexit/signal handlers
        self._registered = True
    
    def run_cleanup(self) -> None:
        """Run all cleanup callbacks."""
        for callback in reversed(self._callbacks):
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback())
                else:
                    callback()
            except Exception as e:
                logging.error(f"Cleanup error: {e}")
        self._callbacks.clear()


# Global cleanup registry
_cleanup_registry: Optional[CleanupRegistry] = None


def get_cleanup_registry() -> CleanupRegistry:
    """Get the global cleanup registry."""
    global _cleanup_registry
    if _cleanup_registry is None:
        _cleanup_registry = CleanupRegistry()
    return _cleanup_registry


def register_cleanup(callback: Callable) -> None:
    """Register a cleanup callback."""
    get_cleanup_registry().register(callback)
