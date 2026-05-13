"""
OpenClaw Feature Flag System
=============================
Inspired by Claude Code's bun:bundle feature() system.

用法:
    from openclaw.feature_flags import feature, feature_flag

    # 方式1: 装饰器（推荐）
    @feature_flag("TRADING_AUTO_MODE")
    def execute_trade():
        ...

    # 方式2: 直接检查
    if feature("STOCK_MONITOR"):
        enable_stock_monitor()

    # 方式3: 延迟检查（不抛异常）
    if is_feature_enabled("MCP_WEB_SEARCH"):
        load_mcp_web_search()

环境变量规则:
    OPENCLAW_FEATURE_<NAME> = 1/true/yes/on  → 启用
    OPENCLAW_FEATURE_<NAME> = 0/false/no/off → 禁用
    未设置 → 使用 DEFAULT_ENABLED 或抛出异常
"""

import os
import functools
from typing import Callable, Optional, TypeVar, Set

# 已知特性列表（用于文档和验证）
_known_features: Set[str] = {
    # 交易相关
    "TRADING_AUTO_MODE",       # 自动交易模式（定时监控+自动下单）
    "STOCK_MONITOR",           # 股票监控预警
    "STOCK_WATCHER",          # 自选股监控
    "TRADING_STRATEGY",       # 交易策略引擎

    # 系统相关
    "FEISHU_DOC",             # 飞书文档
    "WECOM_DOC",              # 企业微信文档
    "TENCENT_DOCS",           # 腾讯文档
    "MCP_SERVER",             # MCP服务器支持
    "SUBAGENT",               # 子Agent嵌套
    "CRON_NESTED",            # 嵌套定时任务

    # 新功能实验
    "CONTEXT_CACHE",          # 上下文缓存
    "TOOL_REGISTRY",          # 统一工具注册表
    "HEARTBEAT_BATCH",        # 心跳批量检查
    "MARKET_CACHE",           # 行情数据缓存
    "STATS_CACHE",            # 交易统计缓存
}

# 默认启用哪些特性（未设置时视为启用）
_default_enabled: Set[str] = {
    "TRADING_AUTO_MODE",
    "STOCK_MONITOR",
    "CONTEXT_CACHE",
    "HEARTBEAT_BATCH",
}


class FeatureFlagError(Exception):
    """特性标志未定义且无默认值时抛出"""
    pass


def _get_env_key(name: str) -> str:
    """将 FEATURE_NAME 转换为环境变量名"""
    return f"OPENCLAW_FEATURE_{name}"


def feature(name: str, default_enabled: bool = False) -> bool:
    """
    检查特性是否启用。

    Args:
        name: 特性名称（如 "TRADING_AUTO_MODE"）
        default_enabled: 未设置环境变量时的默认值

    Returns:
        True 如果启用，否则 False

    Raises:
        FeatureFlagError: 未知特性且无默认值
    """
    # 未知特性检测（可降级为警告）
    if name not in _known_features:
        import warnings
        warnings.warn(f"[FeatureFlag] Unknown feature: {name}", UserWarning, stacklevel=3)

    env_key = _get_env_key(name)
    value = os.environ.get(env_key)

    if value is None:
        # 未设置：使用默认值
        if default_enabled or name in _default_enabled:
            return True
        return False

    # 解析环境变量值
    normalized = value.lower().strip()
    truthy = {"1", "true", "yes", "on", "enabled"}
    falsy  = {"0", "false", "no", "off", "disabled", ""}

    if normalized in truthy:
        return True
    elif normalized in falsy:
        return False
    else:
        import warnings
        warnings.warn(
            f"[FeatureFlag] Invalid value for {env_key}={value!r}, treating as False",
            UserWarning
        )
        return False


def is_feature_enabled(name: str) -> bool:
    """
    安全版本：未知特性默认返回 False，不抛异常。
    适用于插件/扩展的延迟加载。
    """
    return feature(name, default_enabled=False)


def require_feature(name: str) -> None:
    """
    要求特性必须启用，否则抛出异常。
    用于核心功能的强制依赖检查。
    """
    if not is_feature_enabled(name):
        raise FeatureFlagError(
            f"Required feature '{name}' is not enabled. "
            f"Set { _get_env_key(name) }=1 to enable."
        )


T = TypeVar("T", bound=Callable)


def feature_flag(name: str, enabled: Optional[bool] = None):
    """
    装饰器：根据特性开关决定是否执行函数。

    用法:
        @feature_flag("STOCK_MONITOR")
        def start_stock_monitor():
            ...

        # 或者强制指定启用状态
        @feature_flag("STOCK_MONITOR", enabled=True)
        def always_run():
            ...
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # enabled 参数优先级最高
            should_run = enabled if enabled is not None else feature(name)
            if should_run:
                return func(*args, **kwargs)
            else:
                # 返回 None 或包装结果
                return None
        return wrapper  # type: ignore
    return decorator


def feature_flag_conditional(name: str, if_enabled: Callable, if_disabled: Optional[Callable] = None):
    """
    特性开关的条件执行。

    用法:
        result = feature_flag_conditional(
            "STOCK_MONITOR",
            if_enabled=lambda: start_monitor(),
            if_disabled=lambda: "monitor disabled"
        )
    """
    if feature(name):
        return if_enabled()
    elif if_disabled is not None:
        return if_disabled()
    return None


def list_features() -> dict:
    """列出所有特性及其启用状态（用于调试）"""
    result = {}
    for name in sorted(_known_features):
        result[name] = {
            "enabled": is_feature_enabled(name),
            "env_var": _get_env_key(name),
            "default": name in _default_enabled,
        }
    return result


# ============================================================================
# 模块级延迟加载（参考 Claude Code 的条件 import 模式）
# ============================================================================

def lazy_import(module_name: str, import_func: Callable):
    """
    延迟导入：根据 feature flag 决定是否加载模块。

    用法:
        # 不启用时不加载（节省启动时间）
        mcp_search = lazy_import(
            "openclaw.mcp.web_search",
            lambda: __import__("openclaw.mcp.web_search")
        )
    """
    if not is_feature_enabled(module_name.split(".")[-1].upper()):
        return None
    return import_func()
