"""
OpenClaw Format Utilities
=======================
Inspired by Claude Code's src/utils/format.ts.

格式化工具，支持：
1. 文件大小（KB/MB/GB）
2. 时长（ms → s/m/h/d）
3. 数字（千分位、小数位）
4. 货币（¥）
5. 百分比
6. 日期时间
"""

from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

# ============================================================================
# 文件大小
# ============================================================================

def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    
    kb = size_bytes / 1024
    if kb < 1024:
        val = f"{kb:.1f}"
        val = val.rstrip('0').rstrip('.')
        return f"{val}KB"
    
    mb = kb / 1024
    if mb < 1024:
        val = f"{mb:.1f}"
        val = val.rstrip('0').rstrip('.')
        return f"{val}MB"
    
    gb = mb / 1024
    val = f"{gb:.1f}"
    val = val.rstrip('0').rstrip('.')
    return f"{val}GB"

# ============================================================================
# 时长
# ============================================================================

def format_duration(ms: float, most_significant_only: bool = False) -> str:
    """
    格式化时长
    
    Args:
        ms: 毫秒
        most_significant_only: 只显示最大单位
    
    Examples:
        5000 → "5s"
        65000 → "1m 5s"
        3661000 → "1h 1m 1s"
    """
    if ms <= 0:
        return "0s"
    
    if ms < 1000:
        return f"{ms:.0f}ms"
    
    seconds = int(ms / 1000)
    minutes = seconds // 60
    seconds = seconds % 60
    hours = minutes // 60
    minutes = minutes % 60
    days = hours // 24
    hours = hours % 24
    
    if most_significant_only:
        if days > 0:
            return f"{days}d"
        if hours > 0:
            return f"{hours}h"
        if minutes > 0:
            return f"{minutes}m"
        return f"{seconds}s"
    
    if days > 0:
        parts = [f"{days}d"]
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        return " ".join(parts)
    
    if hours > 0:
        parts = [f"{hours}h"]
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0:
            parts.append(f"{seconds}s")
        return " ".join(parts)
    
    if minutes > 0:
        parts = [f"{minutes}m"]
        if seconds > 0:
            parts.append(f"{seconds}s")
        return " ".join(parts)
    
    return f"{seconds}s"

def format_seconds_short(ms: float) -> str:
    """格式化秒（固定1位小数）"""
    return f"{ms / 1000:.1f}s"

# ============================================================================
# 数字
# ============================================================================

def format_number(n: Union[int, float], decimals: Optional[int] = None) -> str:
    """
    格式化数字（千分位）
    
    Examples:
        1234567 → "1,234,567"
        1234567.89 → "1,234,567.89"
    """
    if decimals is not None:
        return f"{n:,.{decimals}f}"
    return f"{n:,}"

def format_percent(n: float, decimals: int = 1) -> str:
    """格式化百分比"""
    return f"{n * 100:.{decimals}f}%"

def format_ratio(numerator: float, denominator: float, decimals: int = 1) -> str:
    """格式化比率"""
    if denominator == 0:
        return "∞"
    return f"{numerator / denominator:.{decimals}f}x"

# ============================================================================
# 货币
# ============================================================================

def format_currency(amount: float, currency: str = "¥", decimals: int = 2) -> str:
    """
    格式化货币
    
    Examples:
        1234.5 → "¥1,234.50"
    """
    return f"{currency}{amount:,.{decimals}f}"

def format_yuan(amount: float, decimals: int = 2) -> str:
    """格式化人民币"""
    return format_currency(amount, "¥", decimals)

def format_commission(amount: float) -> str:
    """格式化佣金（保留4位小数）"""
    return format_currency(amount, "¥", 4)

# ============================================================================
# 股票价格/数量
# ============================================================================

def format_price(price: float, decimals: int = 2) -> str:
    """格式化股价"""
    return f"¥{price:.{decimals}f}"

def format_shares(shares: int) -> str:
    """格式化股数"""
    return f"{shares:,}"

def format_amount(shares: int, price: float) -> str:
    """格式化交易金额"""
    return f"¥{shares * price:,.2f}"

# ============================================================================
# 日期时间
# ============================================================================

def format_datetime(dt: Optional[datetime] = None, tz_hours: int = 8) -> str:
    """格式化日期时间"""
    if dt is None:
        dt = datetime.now(timezone(timedelta(hours=tz_hours)))
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_date(dt: Optional[datetime] = None, tz_hours: int = 8) -> str:
    """格式化日期"""
    if dt is None:
        dt = datetime.now(timezone(timedelta(hours=tz_hours)))
    return dt.strftime("%Y-%m-%d")

def format_time(dt: Optional[datetime] = None, tz_hours: int = 8) -> str:
    """格式化时间"""
    if dt is None:
        dt = datetime.now(timezone(timedelta(hours=tz_hours)))
    return dt.strftime("%H:%M:%S")

def format_timestamp(ts: Optional[float] = None, tz_hours: int = 8) -> str:
    """格式化时间戳"""
    if ts is None:
        dt = datetime.now(timezone(timedelta(hours=tz_hours)))
    else:
        dt = datetime.fromtimestamp(ts, timezone(timedelta(hours=tz_hours)))
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_time_short(dt: Optional[datetime] = None, tz_hours: int = 8) -> str:
    """格式化短时间（仅时分秒）"""
    if dt is None:
        dt = datetime.now(timezone(timedelta(hours=tz_hours)))
    return dt.strftime("%H:%M:%S")

def format_relative_time(dt: datetime, tz_hours: int = 8) -> str:
    """格式化相对时间"""
    now = datetime.now(timezone(timedelta(hours=tz_hours)))
    diff = now - dt
    
    seconds = diff.total_seconds()
    if seconds < 60:
        return "刚刚"
    if seconds < 3600:
        return f"{int(seconds / 60)}分钟前"
    if seconds < 86400:
        return f"{int(seconds / 3600)}小时前"
    if seconds < 604800:
        return f"{int(seconds / 86400)}天前"
    return dt.strftime("%m-%d")

# ============================================================================
# 交易专用格式化
# ============================================================================

def format_trade_record(action: str, stock: str, shares: int, price: float, 
                       reason: str = "") -> str:
    """格式化交易记录"""
    amount = shares * price
    action_emoji = "📈" if action.upper() == "BUY" else "📉"
    return (
        f"{action_emoji} {action.upper()} {stock} "
        f"{shares}股 @ ¥{price:.2f} "
        f"合计 ¥{amount:,.2f}"
        + (f"\n📝 {reason}" if reason else "")
    )

def format_position_summary(stock: str, shares: int, avg_cost: float, 
                          current_price: float) -> dict:
    """格式化持仓汇总"""
    cost = shares * avg_cost
    market_value = shares * current_price
    profit = market_value - cost
    profit_rate = (profit / cost * 100) if cost > 0 else 0
    
    return {
        "stock": stock,
        "shares": f"{shares:,}",
        "avg_cost": f"¥{avg_cost:.3f}",
        "current_price": f"¥{current_price:.3f}",
        "cost": f"¥{cost:,.2f}",
        "market_value": f"¥{market_value:,.2f}",
        "profit": f"¥{profit:,.2f}",
        "profit_rate": f"{profit_rate:+.2f}%",
        "profit_emoji": "🟢" if profit >= 0 else "🔴"
    }

def format_signal(strategy: str, stock: str, signal: str, strength: float) -> str:
    """格式化策略信号"""
    signal_emoji = "🟢" if signal.upper() in ("BUY", "LONG") else \
                   "🔴" if signal.upper() in ("SELL", "SHORT") else "⚪"
    return (
        f"{signal_emoji} [{strategy}] {stock}: {signal} "
        f"(强度: {strength:.0%})"
    )

# ============================================================================
# 颜色输出（ANSI）
# ============================================================================

class Colors:
    """ANSI 颜色码"""
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"

def color_text(text: str, color: str) -> str:
    """给文本添加颜色"""
    return f"{color}{text}{Colors.RESET}"

def green(text: str) -> str:
    return color_text(text, Colors.GREEN)

def red(text: str) -> str:
    return color_text(text, Colors.RED)

def yellow(text: str) -> str:
    return color_text(text, Colors.YELLOW)

def cyan(text: str) -> str:
    return color_text(text, Colors.CYAN)

def format_profit_loss(value: float, show_sign: bool = True) -> str:
    """格式化盈亏（带颜色）"""
    prefix = "+" if show_sign and value > 0 else ""
    colored = green if value >= 0 else red
    return colored(f"{prefix}¥{value:,.2f}")
