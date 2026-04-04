"""
Code indexing tool detection utilities.

Detects usage of common code indexing solutions like Sourcegraph, Cody, etc.
via CLI commands and MCP server integrations.
"""

import re
from typing import List, Optional, Tuple


# Known code indexing tool identifiers
CODE_INDEXING_TOOLS = [
    # Code search engines
    'sourcegraph',
    'hound',
    'seagoat',
    'bloop',
    'gitloop',
    # AI coding assistants with indexing
    'cody',
    'aider',
    'continue',
    'github-copilot',
    'cursor',
    'tabby',
    'codeium',
    'tabnine',
    'augment',
    'windsurf',
    'aide',
    'pieces',
    'qodo',
    'amazon-q',
    'gemini',
    # MCP code indexing servers
    'claude-context',
    'code-index-mcp',
    'local-code-search',
    'autodev-codebase',
    # Context providers
    'openctx',
]


# Mapping of CLI command prefixes to code indexing tools
CLI_COMMAND_MAPPING = {
    # Sourcegraph ecosystem
    'src': 'sourcegraph',
    'cody': 'cody',
    # AI coding assistants
    'aider': 'aider',
    'tabby': 'tabby',
    'tabnine': 'tabnine',
    'augment': 'augment',
    'pieces': 'pieces',
    'qodo': 'qodo',
    'aide': 'aide',
    # Code search tools
    'hound': 'hound',
    'seagoat': 'seagoat',
    'bloop': 'bloop',
    'gitloop': 'gitloop',
    # Cloud provider AI assistants
    'q': 'amazon-q',
    'gemini': 'gemini',
}


# MCP server patterns: (regex_pattern, tool_name)
MCP_SERVER_PATTERNS = [
    # Sourcegraph ecosystem
    (re.compile(r'^sourcegraph$', re.I), 'sourcegraph'),
    (re.compile(r'^cody$', re.I), 'cody'),
    (re.compile(r'^openctx$', re.I), 'openctx'),
    # AI coding assistants
    (re.compile(r'^aider$', re.I), 'aider'),
    (re.compile(r'^continue$', re.I), 'continue'),
    (re.compile(r'^github[-_]?copilot$', re.I), 'github-copilot'),
    (re.compile(r'^copilot$', re.I), 'github-copilot'),
    (re.compile(r'^cursor$', re.I), 'cursor'),
    (re.compile(r'^tabby$', re.I), 'tabby'),
    (re.compile(r'^codeium$', re.I), 'codeium'),
    (re.compile(r'^tabnine$', re.I), 'tabnine'),
    (re.compile(r'^augment[-_]?code$', re.I), 'augment'),
    (re.compile(r'^augment$', re.I), 'augment'),
    (re.compile(r'^windsurf$', re.I), 'windsurf'),
    (re.compile(r'^aide$', re.I), 'aide'),
    (re.compile(r'^codestory$', re.I), 'aide'),
    (re.compile(r'^pieces$', re.I), 'pieces'),
    (re.compile(r'^qodo$', re.I), 'qodo'),
    (re.compile(r'^amazon[-_]?q$', re.I), 'amazon-q'),
    (re.compile(r'^gemini[-_]?code[-_]?assist$', re.I), 'gemini'),
    (re.compile(r'^gemini$', re.I), 'gemini'),
    # Code search tools
    (re.compile(r'^hound$', re.I), 'hound'),
    (re.compile(r'^seagoat$', re.I), 'seagoat'),
    (re.compile(r'^bloop$', re.I), 'bloop'),
    (re.compile(r'^gitloop$', re.I), 'gitloop'),
    # MCP code indexing servers
    (re.compile(r'^claude[-_]?context$', re.I), 'claude-context'),
    (re.compile(r'^code[-_]?index[-_]?mcp$', re.I), 'code-index-mcp'),
    (re.compile(r'^code[-_]?index$', re.I), 'code-index-mcp'),
    (re.compile(r'^local[-_]?code[-_]?search$', re.I), 'local-code-search'),
    (re.compile(r'^codebase$', re.I), 'autodev-codebase'),
    (re.compile(r'^autodev[-_]?codebase$', re.I), 'autodev-codebase'),
    (re.compile(r'^code[-_]?context$', re.I), 'claude-context'),
]


def detect_code_indexing_from_command(command: str) -> Optional[str]:
    """
    Detect if a bash command is using a code indexing CLI tool.

    Args:
        command: The full bash command string

    Returns:
        The code indexing tool identifier, or None if not detected

    Example:
        detect_code_indexing_from_command('src search "pattern"')  # -> 'sourcegraph'
        detect_code_indexing_from_command('cody chat --message "help"')  # -> 'cody'
        detect_code_indexing_from_command('ls -la')  # -> None
    """
    trimmed = command.strip()
    if not trimmed:
        return None

    parts = trimmed.split()
    first_word = parts[0].lower() if parts else ''

    if not first_word:
        return None

    # Check for npx/bunx prefixed commands
    if first_word in ('npx', 'bunx'):
        if len(parts) > 1:
            second_word = parts[1].lower()
            return CLI_COMMAND_MAPPING.get(second_word)
        return None

    return CLI_COMMAND_MAPPING.get(first_word)


def detect_code_indexing_from_mcp_tool(tool_name: str) -> Optional[str]:
    """
    Detect if an MCP tool is from a code indexing server.

    MCP tool names follow the format: mcp__serverName__toolName

    Args:
        tool_name: The MCP tool name (e.g., 'mcp__sourcegraph__search')

    Returns:
        The code indexing tool identifier, or None if not detected

    Example:
        detect_code_indexing_from_mcp_tool('mcp__sourcegraph__search')  # -> 'sourcegraph'
        detect_code_indexing_from_mcp_tool('mcp__cody__chat')  # -> 'cody'
        detect_code_indexing_from_mcp_tool('mcp__filesystem__read')  # -> None
    """
    if not tool_name.startswith('mcp__'):
        return None

    parts = tool_name.split('__')
    if len(parts) < 3:
        return None

    server_name = parts[1]
    if not server_name:
        return None

    return detect_code_indexing_from_mcp_server_name(server_name)


def detect_code_indexing_from_mcp_server_name(server_name: str) -> Optional[str]:
    """
    Detect if an MCP server name corresponds to a code indexing tool.

    Args:
        server_name: The MCP server name

    Returns:
        The code indexing tool identifier, or None if not detected

    Example:
        detect_code_indexing_from_mcp_server_name('sourcegraph')  # -> 'sourcegraph'
        detect_code_indexing_from_mcp_server_name('filesystem')  # -> None
    """
    for pattern, tool in MCP_SERVER_PATTERNS:
        if pattern.match(server_name):
            return tool
    return None


def detect_code_indexing_tool(value: str) -> Optional[str]:
    """
    Unified detection function for code indexing tools.

    Tries all detection methods (command, MCP tool, server name).

    Args:
        value: A command string, MCP tool name, or server name

    Returns:
        The code indexing tool identifier, or None if not detected
    """
    # Try as MCP tool first
    result = detect_code_indexing_from_mcp_tool(value)
    if result:
        return result

    # Try as server name
    result = detect_code_indexing_from_mcp_server_name(value)
    if result:
        return result

    # Try as command
    result = detect_code_indexing_from_command(value)
    return result
