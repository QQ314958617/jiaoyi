"""
OpenClaw MCP Client
====================
Inspired by Claude Code's src/services/mcp/client.ts (3348 lines).

核心设计：
1. MCP 协议：JSON-RPC over HTTP/Streamable
2. Session 管理：connect/disconnect/reconnect
3. Tool 调用：callMcpTool with timeout/caching
4. Auth 缓存：McpAuthCache with TTL
5. 多服务器支持：ServerConfig + ServerCache

Claude Code 的 MCP 设计：
- MCP server = 提供 tools/resources/commands 的外部服务
- connectToServer = 建立到 MCP server 的连接
- fetchToolsForClient = 获取 server 提供的工具（带 LRU 缓存）
- callMcpTool = 调用工具（带超时、错误处理）
- mcpToolInputToAutoClassifierInput = 工具输入转分类器输入
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
import queue


# ============================================================================
# MCP 协议类型
# ============================================================================

class McpMessageType(str, Enum):
    """MCP 消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class McpRequest:
    """MCP 请求"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: str = ""
    params: Optional[Dict] = None


@dataclass
class McpResponse:
    """MCP 响应"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[Dict] = None


@dataclass
class McpTool:
    """MCP 工具"""
    name: str
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    # 元数据
    server_name: str = ""        # 来自哪个服务器
    server_id: str = ""          # 服务器 ID
    # 缓存
    cached: bool = False


@dataclass
class McpResource:
    """MCP 资源"""
    uri: str
    name: str = ""
    description: str = ""
    mime_type: Optional[str] = None


@dataclass
class McpCommand:
    """MCP 命令（对应 Skill）"""
    name: str
    description: str = ""
    prompt: str = ""


# ============================================================================
# MCP 服务器配置
# ============================================================================

@dataclass
class McpServerConfig:
    """MCP 服务器配置"""
    id: str
    name: str
    command: str              # 启动命令，如 "npx", "python"
    args: List[str] = field(default_factory=list)  # 命令参数
    env: Dict[str, str] = field(default_factory=dict)  # 环境变量
    url: Optional[str] = None  # HTTP URL（如果是远程服务器）
    # 认证
    auth_token: Optional[str] = None
    # 连接选项
    timeout_ms: int = 60000
    max_retries: int = 3


# ============================================================================
# MCP Session
# ============================================================================

class McpSession:
    """
    MCP 会话。

    管理到单个 MCP 服务器的连接和通信。
    """

    def __init__(
        self,
        config: McpServerConfig,
        on_tools_changed: Optional[Callable[[List[McpTool]], None]] = None,
    ):
        self.config = config
        self._tools: List[McpTool] = []
        self._resources: List[McpResource] = []
        self._commands: List[McpCommand] = []
        self._connected = False
        self._session_id: Optional[str] = None
        self._lock = threading.RLock()
        self._on_tools_changed = on_tools_changed
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._request_id = 0

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def tools(self) -> List[McpTool]:
        return list(self._tools)

    @property
    def resources(self) -> List[McpResource]:
        return list(self._resources)

    @property
    def commands(self) -> List[McpCommand]:
        return list(self._commands)

    async def connect(self) -> bool:
        """
        连接到 MCP 服务器。

        对应 Claude Code 的 connectToServer()。
        """
        with self._lock:
            if self._connected:
                return True

            try:
                # 如果有 URL，使用 HTTP 连接
                if self.config.url:
                    return await self._connect_http()
                else:
                    # 否则启动进程
                    return await self._connect_process()

            except Exception as e:
                print(f"MCP connection failed: {e}")
                return False

    async def _connect_http(self) -> bool:
        """HTTP 连接（远程 MCP 服务器）"""
        # 发送 initialize 请求
        request = McpRequest(
            id=self._next_id(),
            method="initialize",
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "commands": {},
                },
                "clientInfo": {
                    "name": "openclaw",
                    "version": "1.0.0",
                },
            },
        )

        response = await self._send_request(request)
        if response and response.result:
            self._session_id = response.result.get("sessionId")
            self._connected = True

            # 初始化完成后，发送 notifications/initialized
            await self._send_notification("notifications/initialized", {})

            # 获取可用工具
            await self._fetch_tools()
            return True

        return False

    async def _connect_process(self) -> bool:
        """进程连接（本地 MCP 服务器）"""
        # TODO: 实现 subprocess 启动和通信
        return False

    async def disconnect(self) -> None:
        """断开连接"""
        with self._lock:
            if not self._connected:
                return

            try:
                await self._send_notification("exit", {})
            except Exception:
                pass

            self._connected = False
            self._session_id = None
            self._tools = []
            self._resources = []
            self._commands = []

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        调用 MCP 工具。

        对应 Claude Code 的 callMcpTool()。
        """
        if not self._connected:
            raise McpError(f"MCP session not connected: {self.config.id}")

        timeout = timeout_ms or self.config.timeout_ms

        request = McpRequest(
            id=self._next_id(),
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments,
            },
        )

        response = await self._send_request(request, timeout=timeout)

        if response.error:
            raise McpError(f"MCP tool call failed: {response.error}")

        return response.result or {}

    async def list_tools(self) -> List[McpTool]:
        """列出所有工具"""
        if not self._connected:
            return []
        return list(self._tools)

    async def list_resources(self) -> List[McpResource]:
        """列出所有资源"""
        if not self._connected:
            return []
        return list(self._resources)

    async def list_commands(self) -> List[McpCommand]:
        """列出所有命令（对应 Skills）"""
        if not self._connected:
            return []
        return list(self._commands)

    # ---------------------
    # 内部方法
    # ---------------------

    def _next_id(self) -> str:
        self._request_id += 1
        return str(self._request_id)

    async def _send_request(
        self,
        request: McpRequest,
        timeout: int = 60000,
    ) -> Optional[McpResponse]:
        """发送请求并等待响应"""
        # TODO: 实现 HTTP 请求
        await asyncio.sleep(0.01)
        return None

    async def _send_notification(
        self,
        method: str,
        params: Dict[str, Any],
    ) -> None:
        """发送通知（不需要响应）"""
        pass

    async def _fetch_tools(self) -> None:
        """获取服务器提供的工具列表"""
        request = McpRequest(
            id=self._next_id(),
            method="tools/list",
        )

        response = await self._send_request(request)
        if response and response.result:
            tools = response.result.get("tools", [])
            self._tools = [
                McpTool(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {}),
                    server_name=self.config.name,
                    server_id=self.config.id,
                )
                for t in tools
            ]

            if self._on_tools_changed:
                self._on_tools_changed(self._tools)


class McpError(Exception):
    """MCP 相关错误"""
    pass


# ============================================================================
# MCP 服务器管理器
# ============================================================================

class McpServerManager:
    """
    MCP 服务器管理器。

    管理所有 MCP 服务器连接，支持多服务器。
    """

    _instance: Optional["McpServerManager"] = None
    _lock = threading.RLock()

    def __init__(self):
        self._sessions: Dict[str, McpSession] = {}
        self._configs: Dict[str, McpServerConfig] = {}
        self._tools_cache: Dict[str, List[McpTool]] = {}  # server_id -> tools
        self._cache_time: Dict[str, float] = {}  # server_id -> last_fetch_time
        self._cache_ttl: float = 300  # 5 minutes
        self._lock_internal = threading.RLock()

    @classmethod
    def get_instance(cls) -> "McpServerManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ---------------------
    # 服务器管理
    # ---------------------

    def add_server(self, config: McpServerConfig) -> None:
        """添加 MCP 服务器配置"""
        with self._lock:
            self._configs[config.id] = config

    def remove_server(self, server_id: str) -> bool:
        """移除服务器"""
        with self._lock:
            if server_id in self._sessions:
                asyncio.create_task(self._sessions[server_id].disconnect())
                del self._sessions[server_id]
            if server_id in self._configs:
                del self._configs[server_id]
            return True

    async def connect_server(self, server_id: str) -> bool:
        """连接到服务器"""
        with self._lock:
            if server_id not in self._configs:
                raise McpError(f"Server config not found: {server_id}")

            config = self._configs[server_id]
            session = McpSession(config)
            self._sessions[server_id] = session

            return await session.connect()

    async def disconnect_server(self, server_id: str) -> None:
        """断开服务器连接"""
        with self._lock:
            if server_id in self._sessions:
                await self._sessions[server_id].disconnect()
                del self._sessions[server_id]

    # ---------------------
    # 工具获取
    # ---------------------

    async def get_tools(
        self,
        server_id: Optional[str] = None,
        force_refresh: bool = False,
    ) -> List[McpTool]:
        """
        获取 MCP 工具。

        对应 Claude Code 的 fetchToolsForClient()。
        支持缓存（LRU，TTL 5分钟）。
        """
        if server_id:
            return await self._get_tools_for_server(server_id, force_refresh)
        else:
            # 获取所有服务器的 tools
            all_tools = []
            for sid in self._configs:
                tools = await self._get_tools_for_server(sid, force_refresh)
                all_tools.extend(tools)
            return all_tools

    async def _get_tools_for_server(
        self,
        server_id: str,
        force_refresh: bool = False,
    ) -> List[McpTool]:
        """获取指定服务器的 tools"""
        # 检查缓存
        if not force_refresh and server_id in self._tools_cache:
            cache_time = self._cache_time.get(server_id, 0)
            if time.time() - cache_time < self._cache_ttl:
                return self._tools_cache[server_id]

        # 检查会话
        with self._lock:
            if server_id not in self._sessions:
                await self.connect_server(server_id)

            session = self._sessions.get(server_id)
            if not session or not session.is_connected:
                return []

        # 获取 tools
        tools = await session.list_tools()

        # 更新缓存
        with self._lock_internal:
            self._tools_cache[server_id] = tools
            self._cache_time[server_id] = time.time()

        return tools

    def get_tool(
        self,
        tool_name: str,
        server_id: Optional[str] = None,
    ) -> Optional[McpTool]:
        """获取单个 tool"""
        with self._lock_internal:
            if server_id:
                for tool in self._tools_cache.get(server_id, []):
                    if tool.name == tool_name:
                        return tool
            else:
                # 搜索所有服务器
                for tools in self._tools_cache.values():
                    for tool in tools:
                        if tool.name == tool_name:
                            return tool
        return None

    # ---------------------
    # 工具调用
    # ---------------------

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_id: Optional[str] = None,
        timeout_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        调用 MCP 工具。

        对应 Claude Code 的 callMcpTool()。
        自动根据 tool_name 路由到正确的服务器。
        """
        # 解析 tool_name（格式: mcp__server__tool）
        if tool_name.startswith("mcp__"):
            parts = tool_name.split("__")
            if len(parts) >= 3:
                server_id = parts[1]
                tool_name = parts[2]

        if not server_id:
            # 从缓存中查找
            tool = self.get_tool(tool_name)
            if tool:
                server_id = tool.server_id
            else:
                raise McpError(f"Cannot determine server for tool: {tool_name}")

        with self._lock:
            if server_id not in self._sessions:
                await self.connect_server(server_id)

            session = self._sessions[server_id]
            if not session.is_connected:
                raise McpError(f"Server not connected: {server_id}")

        return await session.call_tool(tool_name, arguments, timeout_ms)

    # ---------------------
    # 资源/命令
    # ---------------------

    async def get_resources(
        self,
        server_id: Optional[str] = None,
    ) -> List[McpResource]:
        """获取 MCP 资源"""
        if server_id:
            with self._lock:
                if server_id not in self._sessions:
                    return []
                return await self._sessions[server_id].list_resources()
        else:
            all_resources = []
            for sid in self._sessions:
                resources = await self.get_resources(sid)
                all_resources.extend(resources)
            return all_resources

    async def get_commands(
        self,
        server_id: Optional[str] = None,
    ) -> List[McpCommand]:
        """获取 MCP 命令（对应 Skills）"""
        if server_id:
            with self._lock:
                if server_id not in self._sessions:
                    return []
                return await self._sessions[server_id].list_commands()
        else:
            all_commands = []
            for sid in self._sessions:
                commands = await self.get_commands(sid)
                all_commands.extend(commands)
            return all_commands

    # ---------------------
    # 统计
    # ---------------------

    def stats(self) -> Dict[str, Any]:
        """统计信息"""
        with self._lock:
            return {
                "servers_total": len(self._configs),
                "servers_connected": sum(
                    1 for s in self._sessions.values() if s.is_connected
                ),
                "tools_cached": sum(
                    len(tools) for tools in self._tools_cache.values()
                ),
                "cache_ttl": self._cache_ttl,
            }


# 全局单例
mcp_server_manager = McpServerManager.get_instance()


# ============================================================================
# MCP Auth 缓存
# ============================================================================

@dataclass
class McpAuthCacheEntry:
    """认证缓存条目"""
    server_id: str
    access_token: str
    expires_at: float


class McpAuthCache:
    """
    MCP 认证缓存。

    对应 Claude Code 的 getMcpAuthCache() / setMcpAuthCacheEntry()。
    TTL 15 分钟。
    """

    _instance: Optional["McpAuthCache"] = None
    _lock = threading.RLock()
    _ttl_ms: int = 15 * 60 * 1000  # 15 min

    def __init__(self):
        self._cache: Dict[str, McpAuthCacheEntry] = {}

    @classmethod
    def get_instance(cls) -> "McpAuthCache":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get(self, server_id: str) -> Optional[str]:
        """获取缓存的 access token"""
        with self._lock:
            entry = self._cache.get(server_id)
            if not entry:
                return None

            # 检查是否过期
            if time.time() * 1000 > entry.expires_at:
                del self._cache[server_id]
                return None

            return entry.access_token

    def set(self, server_id: str, access_token: str) -> None:
        """设置 access token"""
        with self._lock:
            self._cache[server_id] = McpAuthCacheEntry(
                server_id=server_id,
                access_token=access_token,
                expires_at=time.time() * 1000 + self._ttl_ms,
            )

    def clear(self, server_id: Optional[str] = None) -> None:
        """清除缓存"""
        with self._lock:
            if server_id:
                self._cache.pop(server_id, None)
            else:
                self._cache.clear()


# ============================================================================
# MCP 工具到 OpenClaw 工具的桥接
# ============================================================================

class McpToolBridge:
    """
    MCP 工具桥接器。

    将 MCP 工具转换为 OpenClaw 工具格式。
    """

    def __init__(self, manager: Optional[McpServerManager] = None):
        self.manager = manager or mcp_server_manager

    def mcp_tool_to_openclaw_format(
        self,
        mcp_tool: McpTool,
    ) -> Dict[str, Any]:
        """
        将 MCP 工具转换为 OpenClaw 工具格式。

        对应 Claude Code 的 mcpToolInputToAutoClassifierInput。
        """
        return {
            "name": f"mcp__{mcp_tool.server_id}__{mcp_tool.name}",
            "description": mcp_tool.description,
            "input_schema": mcp_tool.input_schema,
            "server": mcp_tool.server_name,
            "server_id": mcp_tool.server_id,
        }

    async def get_all_openclaw_tools(self) -> List[Dict[str, Any]]:
        """获取所有 MCP 工具（OpenClaw 格式）"""
        mcp_tools = await self.manager.get_tools()
        return [
            self.mcp_tool_to_openclaw_format(tool)
            for tool in mcp_tools
        ]

    def format_tool_name(self, server_id: str, tool_name: str) -> str:
        """格式化 MCP 工具名称"""
        return f"mcp__{server_id}__{tool_name}"

    def parse_tool_name(
        self,
        full_name: str,
    ) -> Optional[tuple[str, str]]:
        """解析 MCP 工具名称"""
        if not full_name.startswith("mcp__"):
            return None

        parts = full_name.split("__")
        if len(parts) >= 3:
            return (parts[1], parts[2])
        return None


# 全局桥接器
mcp_tool_bridge = McpToolBridge()


# ============================================================================
# 便捷函数
# ============================================================================

async def connect_mcp_server(
    server_id: str,
    command: str,
    args: Optional[List[str]] = None,
    env: Optional[Dict[str, str]] = None,
    url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> bool:
    """
    快速连接 MCP 服务器。

    用法：
        await connect_mcp_server(
            server_id="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "/path"],
        )
    """
    config = McpServerConfig(
        id=server_id,
        name=server_id,
        command=command,
        args=args or [],
        env=env or {},
        url=url,
        auth_token=auth_token,
    )

    mcp_server_manager.add_server(config)
    return await mcp_server_manager.connect_server(server_id)


async def call_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    timeout_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """
    调用 MCP 工具。

    用法：
        result = await call_mcp_tool(
            "mcp__filesystem__read_file",
            {"path": "/tmp/test.txt"}
        )
    """
    return await mcp_server_manager.call_tool(tool_name, arguments, timeout_ms=timeout_ms)


async def get_mcp_tools(force_refresh: bool = False) -> List[McpTool]:
    """获取所有 MCP 工具"""
    return await mcp_server_manager.get_tools(force_refresh=force_refresh)


def mcp_tool_name(server_id: str, tool_name: str) -> str:
    """生成 MCP 工具全名"""
    return f"mcp__{server_id}__{tool_name}"
