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


# ============================================================================
# Claude Code bashPermissions.ts 设计补充
# ============================================================================
# 以下代码灵感来自 Claude Code 的 bashPermissions.ts (2621行)
# 核心改进：完整的 SAFE_ENV_VARS 白名单、Wrapper 剥离、命令前缀提取
# ============================================================================

# -----------------------------------------------------------------------------
# SAFE_ENV_VARS - 可安全剥离的环境变量白名单
# -----------------------------------------------------------------------------
# 来自 Claude Code 的 SAFE_ENV_VARS 设计
# 安全原则：这些变量不能执行代码或加载库

SAFE_ENV_VARS: Set[str] = {
    # Go - build/runtime settings only
    "GOEXPERIMENT", "GOOS", "GOARCH", "CGO_ENABLED", "GO111MODULE",

    # Rust - logging/debugging only
    "RUST_BACKTRACE", "RUST_LOG",

    # Node - environment name only (not NODE_OPTIONS!)
    "NODE_ENV",

    # Python - behavior flags only (not PYTHONPATH!)
    "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED",

    # Pytest - test configuration
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "PYTEST_DEBUG",

    # API keys and authentication
    "ANTHROPIC_API_KEY",

    # Locale and character encoding
    "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE", "LC_TIME", "CHARSET",

    # Terminal and display
    "TERM", "COLORTERM", "NO_COLOR", "FORCE_COLOR", "TZ",

    # Color configuration
    "LS_COLORS", "LSCOLORS", "GREP_COLOR", "GREP_COLORS", "GCC_COLORS",

    # Display formatting
    "TIME_STYLE", "BLOCK_SIZE", "BLOCKSIZE",
}

# 命令前缀提取的正则
ENV_VAR_ASSIGN_RE = re.compile(r"^[A-Za-z_]\w*=")
SUBCOMMAND_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")

# 裸 Shell 前缀（不能单独作为前缀建议）
BARE_SHELL_PREFIXES: Set[str] = {
    "sh", "bash", "zsh", "fish", "csh", "tcsh", "ksh", "dash",
    "cmd", "powershell", "pwsh",
    "env", "xargs",
    "nice", "stdbuf", "nohup", "timeout", "time",
    "sudo", "doas", "pkexec",
}


def get_simple_command_prefix(command: str) -> Optional[str]:
    """
    提取命令前缀（命令 + 子命令）。

    对应 Claude Code 的 getSimpleCommandPrefix。
    例如：
        'git commit -m "fix"' → 'git commit'
        'ls -la' → None (flag, not subcommand)
        'python3 script.py' → None (filename, not subcommand)

    Returns:
        命令前缀字符串，或 None
    """
    import shlex
    try:
        tokens = shlex.split(command.strip())
    except ValueError:
        return None

    if not tokens:
        return None

    # 跳过环境变量赋值
    i = 0
    while i < len(tokens) and ENV_VAR_ASSIGN_RE.match(tokens[i]):
        i += 1

    remaining = tokens[i:]
    if len(remaining) < 2:
        return None

    # 第二个 token 必须是子命令（不是 flag/文件名/路径/数字）
    subcmd = remaining[1]
    if not SUBCOMMAND_RE.match(subcmd):
        return None

    return f"{remaining[0]} {subcmd}"


def get_first_word_prefix(command: str) -> Optional[str]:
    """
    回退方案：提取第一个单词作为前缀。

    对应 Claude Code 的 getFirstWordPrefix。
    例如：'python3 script.py' → 'python3'
    """
    import shlex
    try:
        tokens = shlex.split(command.strip())
    except ValueError:
        return None

    if not tokens:
        return None

    # 跳过环境变量赋值
    i = 0
    while i < len(tokens) and ENV_VAR_ASSIGN_RE.match(tokens[i]):
        i += 1

    if i >= len(tokens):
        return None

    cmd = tokens[i]
    # 不能是裸 shell 前缀
    if cmd in BARE_SHELL_PREFIXES or not SUBCOMMAND_RE.match(cmd):
        return None

    return cmd


def strip_safe_wrappers(command: str) -> str:
    """
    剥离安全的命令包装器。

    对应 Claude Code 的 stripSafeWrappers。
    剥离：timeout, time, nice, stdbuf, nohup 等包装命令。
    这些包装器本身是安全的，只是执行其参数。
    """
    stripped = command.strip()

    # timeout 剥离
    # 例如: timeout 30s python3 script.py
    timeout_pattern = re.compile(
        r"^timeout(?:\s+--?\w+(?:=\S+|\s+\S+)?)*\s+\d+(?:\.\d+)?[smhd]?\s+"
    )
    stripped = timeout_pattern.sub("", stripped)

    # time 剥离
    time_pattern = re.compile(r"^time\s+")
    stripped = time_pattern.sub("", stripped)

    # nice 剥离
    # 例如: nice -n 10 python3 script.py
    nice_pattern = re.compile(r"^nice(?:\s+-n\s+\d+|\s+-\d+)?\s+")
    stripped = nice_pattern.sub("", stripped)

    # stdbuf 剥离
    # 例如: stdbuf -o0 python3 script.py
    stdbuf_pattern = re.compile(r"^stdbuf(?:\s+-[ioe][LN0-9]+)+\s+")
    stripped = stdbuf_pattern.sub("", stripped)

    # nohup 剥离
    nohup_pattern = re.compile(r"^nohup\s+")
    stripped = nohup_pattern.sub("", stripped)

    return stripped


def strip_all_leading_env_vars(command: str) -> str:
    """
    剥离命令开头的环境变量赋值。

    对应 Claude Code 的 stripAllLeadingEnvVars。
    例如: 'NODE_ENV=prod npm run build' → 'npm run build'
    """
    import shlex
    try:
        tokens = shlex.split(command.strip())
    except ValueError:
        return command

    if not tokens:
        return command

    result = []
    i = 0
    for i, token in enumerate(tokens):
        if ENV_VAR_ASSIGN_RE.match(token):
            var_name = token.split("=")[0]
            if var_name in SAFE_ENV_VARS:
                continue  # 剥离这个 token
        result.append(token)

    return " ".join(result)


def normalize_command(command: str) -> str:
    """
    标准化命令：剥离注释、空格、环境变量、包装器。

    对应 Claude Code 的完整命令标准化流程。
    """
    import shlex
    # 去除注释
    lines = command.split("\n")
    non_comment = [
        line for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]
    command = "\n".join(non_comment)

    # 剥离环境变量
    command = strip_all_leading_env_vars(command)

    # 剥离包装器
    command = strip_safe_wrappers(command)

    return command.strip()


def suggest_permission_rule(command: str) -> str:
    """
    为命令生成权限规则建议。

    对应 Claude Code 的 suggestionForExactCommand/suggestionForPrefix。
    返回：精确匹配规则 或 前缀匹配规则。
    """
    # 标准化命令
    normalized = normalize_command(command)

    # 尝试提取命令前缀
    prefix = get_simple_command_prefix(normalized)
    if prefix:
        return f"Bash({prefix}:*)"

    # 回退到第一单词
    first_word = get_first_word_prefix(normalized)
    if first_word:
        return f"Bash({first_word}:*)"

    # 最末回退：精确匹配
    return f"Bash({normalized}:*)"


# -----------------------------------------------------------------------------
# 命令语义检查（增强版）
# -----------------------------------------------------------------------------
# 危险命令的语义检查，不仅仅依赖模式匹配

DANGEROUS_COMMANDS: Set[str] = {
    # 文件删除/格式化
    "rm", "del", "rmdir", "mkfs", "fdisk", "dd",
    # 网络后门
    "nc", "ncat", "netcat", "socat",
    # 权限修改
    "chmod", "chown", "chgrp",
    # 系统修改
    "sysctl", "mount", "umount", "modprobe", "insmod",
    # 进程终止
    "kill", "killall", "pkill",
    # 下载执行
    "curl|sh", "wget|sh", "bash -c", "sh -c",
}


def check_command_semantics(command: str) -> Tuple[bool, str]:
    """
    检查命令语义层面的安全性。

    对应 Claude Code 的 checkSemanticsDeny。
    比正则更深入地检查命令的实际意图。
    """
    import shlex
    normalized = normalize_command(command)

    try:
        tokens = shlex.split(normalized)
    except ValueError:
        return True, ""  # 无法解析，跳过

    if not tokens:
        return True, ""

    base_cmd = tokens[0]

    # 危险命令黑名单
    if base_cmd in {
        "rm", "del", "rmdir",
        "mkfs", "fdisk", "dd",
        "chmod", "chown", "chgrp",
        "mount", "umount",
        "sysctl", "modprobe", "insmod",
        "kill", "killall", "pkill",
    }:
        return False, f"危险命令: {base_cmd}"

    # 管道危险组合
    if "|" in command or "&&" in command:
        # curl|sh, wget|sh 等下载执行模式
        dangerous_combo = any(
            combo in command.lower()
            for combo in ["curl|sh", "wget|sh", "bash -c", "sh -c", "|sh", "| bash"]
        )
        if dangerous_combo:
            return False, "危险的管道命令组合"

    # eval / source with variable
    if base_cmd in {"eval", "source"}:
        return False, f"潜在危险的命令: {base_cmd}"

    return True, ""


# -----------------------------------------------------------------------------
# 路径约束（增强版）
# -----------------------------------------------------------------------------

def check_path_constraints(
    command: str,
    constraint: Optional[PathConstraint] = None
) -> Tuple[bool, str]:
    """
    检查命令的路径约束（增强版）。

    基于 Claude Code 的 checkPathConstraints。
    包含更完善的路径遍历检测。
    """
    import shlex

    if constraint is None:
        constraint = DEFAULT_PATH_CONSTRAINT

    try:
        tokens = shlex.split(command)
    except ValueError:
        return True, ""

    for token in tokens:
        # 跳过选项和 URL
        if token.startswith("-") or "://" in token:
            continue
        # 跳过常见系统路径
        if token.startswith("/bin/") or token.startswith("/usr/bin/"):
            continue
        # 跳过环境变量
        if "=" in token and not token.startswith("-"):
            continue

        # 清理可能的引号
        clean = token.strip("'\"")

        # 检查路径
        if clean.startswith("/") and not constraint.is_allowed(clean):
            return False, f"路径不在允许范围内: {clean}"

        # 检查 cd .. 逃逸
        if "cd .." in command or command.startswith("cd .."):
            # 检查 cd 目标
            for i, t in enumerate(tokens):
                if t == "cd" and i + 1 < len(tokens):
                    target = tokens[i + 1]
                    if not constraint.is_allowed(target):
                        return False, f"cd 目标不允许: {target}"

    return True, ""
