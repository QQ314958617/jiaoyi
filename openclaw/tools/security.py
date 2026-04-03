"""
OpenClaw Security Module
==========================
Inspired by Claude Code's bashPermissions.ts (2621 lines) and bashSecurity.ts.

核心功能：
1. 危险命令检测
2. 路径约束（限制 exec 可访问的目录）
3. PermissionRule 规则引擎
4. Bash 命令 AST 分析（基础版）
5. 沙箱执行支持

Claude Code 的权限模型：
- PermissionRule: 规则定义（tool + pattern + behavior）
- bashClassifier: AI 辅助判断命令是否危险
- pathValidation: 路径约束（防止 cd .. 逃逸）
- sedValidation: sed 命令约束
- shouldUseSandbox: 沙箱降级
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set, Tuple
from enum import Enum

from openclaw.tools.base import (
    PermissionRule, PermissionBehavior, PermissionCheckResult,
    DANGEROUS_PATTERNS, is_dangerous_command,
)


# ============================================================================
# 路径约束
# ============================================================================

@dataclass
class PathConstraint:
    """
    路径约束配置。

    限制 exec 命令只能在指定目录树内操作。
    防止 `cd / && rm -rf .` 逃逸。
    """
    allowed_paths: List[str] = field(default_factory=list)  # 允许的根路径
    denied_paths: List[str] = field(default_factory=list)   # 拒绝的路径
    deny_parent_access: bool = True  # 是否拒绝 .. 逃逸

    def is_allowed(self, path: str) -> bool:
        """检查路径是否允许访问"""
        # 规范化路径
        abs_path = os.path.abspath(os.path.expanduser(path))

        # 检查是否在允许路径内
        for allowed in self.allowed_paths:
            allowed_abs = os.path.abspath(os.path.expanduser(allowed))
            if abs_path.startswith(allowed_abs + os.sep) or abs_path == allowed_abs:
                break
        else:
            # 不在任何一个允许路径内
            if self.allowed_paths:
                return False

        # 检查是否在拒绝路径内
        for denied in self.denied_paths:
            denied_abs = os.path.abspath(os.path.expanduser(denied))
            if abs_path.startswith(denied_abs + os.sep) or abs_path == denied_abs:
                return False

        return True

    def validate_cwd(self, cwd: str) -> bool:
        """检查工作目录是否合法"""
        return self.is_allowed(cwd)


# 默认路径约束：只能操作 workspace 和 /tmp
DEFAULT_PATH_CONSTRAINT = PathConstraint(
    allowed_paths=["/root/.openclaw/workspace", "/tmp"],
    denied_paths=["/root/.ssh", "/root/.aws", "/etc/ssh"],
    deny_parent_access=True,
)


def check_path_traversal(command: str, constraint: Optional[PathConstraint] = None) -> Tuple[bool, str]:
    """
    检查命令是否存在路径遍历风险。

    Returns:
        (是否安全, 原因)
    """
    if constraint is None:
        constraint = DEFAULT_PATH_CONSTRAINT

    # 检测 cd .. 逃逸
    if "cd .." in command or command.startswith("cd .."):
        if constraint.deny_parent_access:
            return False, "路径遍历 (cd ..) 被拒绝"

    # 检测绝对路径逃逸
    import shlex
    try:
        tokens = shlex.split(command)
    except ValueError:
        return True, ""  # 无法解析，跳过路径检查

    for token in tokens:
        # 跳过常见的系统命令路径和URL
        if token.startswith("/bin/") or token.startswith("/usr/bin/"):
            continue
        if token.startswith("http://") or token.startswith("https://"):
            continue
        if not token.startswith("/"):
            continue
        # 清理可能的引号包裹
        clean = token.strip("'\"").strip()
        if not clean.startswith("/"):
            continue
        if not constraint.is_allowed(clean):
            return False, f"路径不在允许范围内: {clean}"

    return True, ""


# ============================================================================
# Sed 命令约束
# ============================================================================

@dataclass
class SedConstraint:
    """Sed 命令约束"""
    max_size_kb: int = 1024     # 单个文件最大 1MB
    allowed_edits: bool = True   # 是否允许编辑模式
    require_backup: bool = False  # 是否要求备份

    def validate(self, command: str) -> Tuple[bool, str]:
        """验证 sed 命令"""
        if not self.allowed_edits:
            return False, "Sed editing is disabled"

        # 检测危险 sed 模式
        dangerous_sed = [
            r"sed.*-i.*/",  # sed -i（原地编辑）
            r"sed.*%.*%.*g",  # 全局替换
        ]

        for pattern in dangerous_sed:
            if re.search(pattern, command):
                return False, f"Dangerous sed pattern: {pattern}"

        return True, ""


# ============================================================================
# 命令解析器（基础 AST）
# ============================================================================

@dataclass
class ParsedCommand:
    """解析后的命令"""
    raw: str
    command_name: str           # 第一个词（命令名）
    args: List[str] = field(default_factory=list)  # 参数列表
    redirections: List[str] = field(default_factory=list)  # 重定向 > >>
    pipes: List[str] = field(default_factory=list)  # 管道 |
    background: bool = False   # 后台运行 &
    env_vars: List[str] = field(default_factory=list)  # VAR=value


def parse_command(command: str) -> ParsedCommand:
    """
    基础命令解析。

    提取：命令名、参数、重定向、管道、环境变量。
    不做复杂的 shell 语法分析。
    """
    import shlex
    try:
        tokens = shlex.split(command)
    except ValueError:
        # 无法解析，返回原始
        return ParsedCommand(raw=command, command_name=command.split()[0] if command else "")

    # 过滤环境变量赋值
    env_vars = [t for t in tokens if "=" in t and not t.startswith("=")]
    tokens = [t for t in tokens if not ("=" in t and not t.startswith("="))]

    # 解析重定向和管道
    redirections = []
    pipes = []
    filtered = []
    for t in tokens:
        if t in (">", ">>", "1>", "2>"):
            redirections.append(t)
        elif t == "|":
            pipes.append("|")
        elif t == "&":
            pass  # 后台运行标记
        else:
            filtered.append(t)

    return ParsedCommand(
        raw=command,
        command_name=filtered[0] if filtered else "",
        args=filtered[1:],
        redirections=redirections,
        pipes=pipes,
        background="&" in command,
        env_vars=env_vars,
    )


# ============================================================================
# Bash 权限分类器
# ============================================================================

class BashPermissionClassifier:
    """
    Bash 命令权限分类器。

    参考 Claude Code 的 bashClassifier.ts。
    对命令进行多维度安全评估。

    分类结果：
    - ALLOW: 允许执行
    - DENY: 拒绝执行
    - ASK: 需要用户确认
    """

    # 安全命令白名单（只读/信息查询）
    SAFE_COMMANDS: Set[str] = {
        "ls", "pwd", "whoami", "date", "echo", "cat", "head", "tail",
        "grep", "find", "which", "whereis", "type", "history",
        "ps", "top", "df", "du", "free", "uptime", "uname", "hostname",
        "curl", "wget", "ping", "nslookup", "dig", "netstat", "ss",
        "git", "svn", "hg",
        "python", "python3", "pip", "pip3",
        "node", "npm", "npx",
        "docker", "docker-compose",
        "kubectl", "helm",
        "aws", "gcloud", "az",
        "vim", "nano", "less", "more",
        "stat", "file", "md5sum", "sha256sum",
        "tar", "zip", "unzip", "gzip", "gunzip",
        "cp", "mv", "mkdir", "touch",
    }

    # 高风险命令（需要特殊权限）
    RISKY_COMMANDS: Set[str] = {
        "rm", "dd", "mkfs", "fdisk", "parted",
        "chmod", "chown", "chgrp",
        "useradd", "userdel", "usermod", "passwd",
        "iptables", "ufw", "firewalld",
        "systemctl", "service", "init",
        "reboot", "shutdown", "halt", "poweroff",
        "kill", "killall", "pkill",
        "sudo", "su",
        "ssh", "scp", "rsync",
        "curl", "wget", "nc", "ncat", "netcat",
    }

    # 破坏性命令（需要明确确认）
    DESTRUCTIVE_COMMANDS: Set[str] = {
        "rm -rf", "rm -r", "rm -f",
        "dd",
        "mkfs",
        ":(){:|:&};:",  # fork bomb
        "> /dev/",  # 设备写入
    }

    def __init__(self, path_constraint: Optional[PathConstraint] = None):
        self.path_constraint = path_constraint or DEFAULT_PATH_CONSTRAINT
        self.sed_constraint = SedConstraint()

    def classify(self, command: str) -> Tuple[str, str]:
        """
        分类命令。

        Returns:
            (ALLOW/DENY/ASK, 原因)
        """
        if not command or not command.strip():
            return "DENY", "Empty command"

        command = command.strip()

        # 1. 危险命令模式检查
        is_dangerous, reason = is_dangerous_command(command)
        if is_dangerous:
            return "DENY", reason

        # 2. 解析命令
        parsed = parse_command(command)
        cmd = parsed.command_name

        # 3. 空命令检查
        if not cmd:
            return "DENY", "Empty command"

        # 4. shell 内建命令检查（允许）
        builtin_commands = {"cd", "export", "source", "alias", "unalias", "set", "unset", "exit", "return"}
        if cmd in builtin_commands:
            return "ALLOW", f"Builtin command: {cmd}"

        # 5. 破坏性命令检查
        for destructive in self.DESTRUCTIVE_COMMANDS:
            if destructive in command:
                return "DENY", f"Destructive command: {destructive}"

        # 6. 路径遍历检查
        safe, reason = check_path_traversal(command, self.path_constraint)
        if not safe:
            return "DENY", reason

        # 7. sed 约束检查
        if cmd == "sed":
            safe, reason = self.sed_constraint.validate(command)
            if not safe:
                return "DENY", reason

        # 8. 高风险命令需要确认
        if cmd in self.RISKY_COMMANDS:
            return "ASK", f"Risky command: {cmd}"

        # 9. 安全命令白名单
        if cmd in self.SAFE_COMMANDS:
            return "ALLOW", f"Safe command: {cmd}"

        # 10. 未知命令 -> 询问
        return "ASK", f"Unknown command: {cmd}"

    def classify_with_rules(
        self,
        command: str,
        rules: List[PermissionRule]
    ) -> PermissionCheckResult:
        """
        结合 PermissionRule 分类。

        规则优先于分类器。
        """
        parsed = parse_command(command)
        input_data = {"command": command, "args": parsed.args}

        # 规则匹配（从后往前，后添加的优先）
        for rule in reversed(rules):
            if rule.tool_name == "exec" or rule.tool_name == "*":
                if rule.rule_content is None:
                    # 通用规则
                    if rule.behavior == PermissionBehavior.DENY:
                        return PermissionCheckResult.deny(
                            reason=f"Blocked: {rule.description}",
                            rule=rule,
                        )
                    elif rule.behavior == PermissionBehavior.ASK:
                        return PermissionCheckResult.ask(
                            reason=f"Requires confirmation: {rule.description}",
                        )
                else:
                    # 内容匹配
                    import fnmatch
                    if fnmatch.fnmatch(command, rule.rule_content):
                        if rule.behavior == PermissionBehavior.DENY:
                            return PermissionCheckResult.deny(
                                reason=f"Blocked: {rule.description}",
                                rule=rule,
                            )
                        elif rule.behavior == PermissionBehavior.ASK:
                            return PermissionCheckResult.ask(
                                reason=f"Requires confirmation: {rule.description}",
                            )

        # 分类器判断
        behavior, reason = self.classify(command)

        if behavior == "ALLOW":
            return PermissionCheckResult.allow(reason)
        elif behavior == "DENY":
            return PermissionCheckResult.deny(reason)
        else:  # ASK
            return PermissionCheckResult.ask(reason)


# ============================================================================
# 安全执行
# ============================================================================

@dataclass
class ExecResult:
    """Exec 执行结果"""
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    execution_time_ms: float = 0.0
    denied: bool = False
    denial_reason: str = ""


def safe_exec(
    command: str,
    cwd: Optional[str] = None,
    timeout: int = 30,
    allow_shell: bool = False,
    rules: Optional[List[PermissionRule]] = None,
    path_constraint: Optional[PathConstraint] = None,
) -> ExecResult:
    """
    安全执行 shell 命令。

    集成权限检查 + 路径约束 + 超时控制。

    Args:
        command: 要执行的命令
        cwd: 工作目录
        timeout: 超时秒数
        allow_shell: 是否允许 shell 扩展
        rules: PermissionRule 列表
        path_constraint: 路径约束

    Returns:
        ExecResult
    """
    import time
    start = time.time()

    # 1. 分类器权限检查
    constraint = path_constraint or DEFAULT_PATH_CONSTRAINT
    classifier = BashPermissionClassifier(constraint)

    if rules:
        permission = classifier.classify_with_rules(command, rules)
    else:
        behavior, reason = classifier.classify(command)
        if behavior == "ALLOW":
            permission = PermissionCheckResult.allow(reason)
        elif behavior == "DENY":
            permission = PermissionCheckResult.deny(reason)
        else:
            permission = PermissionCheckResult.ask(reason)

    if not permission.allowed:
        return ExecResult(
            success=False,
            denied=True,
            denial_reason=permission.reason,
            execution_time_ms=(time.time() - start) * 1000,
        )

    # 2. 执行
    try:
        shell = "/bin/bash" if allow_shell else None
        result = subprocess.run(
            command,
            shell=shell,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return ExecResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            execution_time_ms=(time.time() - start) * 1000,
        )
    except subprocess.TimeoutExpired:
        return ExecResult(
            success=False,
            stderr="Command timed out",
            exit_code=-1,
            execution_time_ms=(time.time() - start) * 1000,
        )
    except Exception as e:
        return ExecResult(
            success=False,
            stderr=str(e),
            exit_code=-1,
            execution_time_ms=(time.time() - start) * 1000,
        )
