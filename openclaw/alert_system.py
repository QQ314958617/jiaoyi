"""
蛋蛋预警系统
功能：
1. 自选股监控列表
2. 涨跌幅异动预警
3. 定时检查并推送通知
"""
import json
import os
import time
import threading
import requests
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


# ============================================================================
# 预警配置
# ============================================================================

WATCHLIST_FILE = "/root/.openclaw/workspace/data/watchlist.json"
ALERTS_FILE = "/root/.openclaw/workspace/data/alerts.json"

# 预警阈值
DEFAULT_PRICE_CHANGE_THRESHOLD = 5.0  # 涨跌幅超过5%
DEFAULT_VOLUME_SPIKE_THRESHOLD = 2.0    # 成交量放大2倍

# 预警冷却时间（秒）
ALERT_COOLDOWN = 300  # 5分钟内不重复预警


# ============================================================================
# 预警数据结构
# ============================================================================

@dataclass
class WatchStock:
    """自选股"""
    code: str
    name: str
    base_price: float = 0       # 参考价（昨日收盘或买入价）
    price_change_threshold: float = 5.0  # 涨跌幅预警阈值
    volume_threshold: float = 2.0        # 量比预警阈值
    enabled: bool = True
    added_at: str = ""


@dataclass
class PriceAlert:
    """预警记录"""
    code: str
    name: str
    alert_type: str  # price_up / price_down / volume_spike
    message: str
    price: float
    change_pct: float
    triggered_at: str
    acknowledged: bool = False


# ============================================================================
# 工具函数
# ============================================================================

def ensure_data_dir():
    """确保数据目录存在"""
    os.makedirs(os.path.dirname(WATCHLIST_FILE), exist_ok=True)


def load_watchlist() -> List[Dict]:
    """加载自选股列表"""
    ensure_data_dir()
    try:
        if os.path.exists(WATCHLIST_FILE):
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []


def save_watchlist(watchlist: List[Dict]):
    """保存自选股列表"""
    ensure_data_dir()
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, ensure_ascii=False, indent=2)


def load_alerts() -> List[Dict]:
    """加载预警记录"""
    ensure_data_dir()
    try:
        if os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return []


def save_alerts(alerts: List[Dict]):
    """保存预警记录"""
    ensure_data_dir()
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(alerts, f, ensure_ascii=False, indent=2)


def get_realtime_quote(code: str) -> Optional[Dict]:
    """获取单只股票实时行情"""
    try:
        prefix = "sh" if code.startswith(("6", "5")) else "sz"
        url = f"https://qt.gtimg.cn/q={prefix}{code}"
        r = requests.get(url, timeout=3)
        fields = r.text.split('="')[1].strip('"').split('~')
        if len(fields) > 10:
            return {
                "code": code,
                "name": fields[1],
                "price": float(fields[3]) if fields[3] != '-' else 0,
                "close": float(fields[4]) if fields[4] != '-' else 0,
                "open": float(fields[5]) if fields[5] != '-' else 0,
                "volume": float(fields[6]) if fields[6] != '-' else 0,
                "change_pct": float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0,
                "high": float(fields[33]) if len(fields) > 33 and fields[33] != '-' else 0,
                "low": float(fields[34]) if len(fields) > 34 and fields[34] != '-' else 0,
                "time": fields[30] if len(fields) > 30 else "",
            }
    except:
        pass
    return None


def get_batch_quotes(codes: List[str]) -> Dict[str, Dict]:
    """批量获取行情"""
    if not codes:
        return {}

    try:
        prefixes = ["sh" if c.startswith(("6", "5")) else "sz" for c in codes]
        code_str = ",".join([f"{p}{c}" for p, c in zip(prefixes, codes)])
        url = f"https://qt.gtimg.cn/q={code_str}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://gu.qq.com/'
        }
        r = requests.get(url, headers=headers, timeout=5)
        result = {}

        for line in r.text.strip().split('\n'):
            if '=' not in line:
                continue
            # 解析代码
            key = line.split('=')[0].replace('v_', '')
            fields = line.split('="')[1].strip('"').split('~')
            if len(fields) < 10:
                continue

            code = key.upper().replace('SH', '').replace('SZ', '')

            result[code] = {
                "code": code,
                "name": fields[1],
                "price": float(fields[3]) if fields[3] != '-' else 0,
                "close": float(fields[4]) if fields[4] != '-' else 0,
                "change_pct": float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0,
                "volume": float(fields[6]) if fields[6] != '-' else 0,
            }

        return result

    except Exception as e:
        print(f"[AlertSystem] Batch quote error: {e}")
        return {}


# ============================================================================
# 预警核心逻辑
# ============================================================================

def check_watchlist_alerts() -> List[PriceAlert]:
    """
    检查所有自选股，生成预警列表
    """
    watchlist = load_watchlist()
    if not watchlist:
        return []

    codes = [w["code"] for w in watchlist if w.get("enabled", True)]
    if not codes:
        return []

    quotes = get_batch_quotes(codes)
    alerts = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for stock in watchlist:
        if not stock.get("enabled", True):
            continue

        code = stock["code"]
        if code not in quotes:
            continue

        quote = quotes[code]
        current_price = quote.get("price", 0)
        change_pct = quote.get("change_pct", 0)
        base_price = stock.get("base_price", quote.get("close", 0))

        # 检查涨跌幅预警
        threshold = stock.get("price_change_threshold", DEFAULT_PRICE_CHANGE_THRESHOLD)

        if base_price > 0:
            actual_change = ((current_price - base_price) / base_price) * 100
        else:
            actual_change = change_pct

        if abs(actual_change) >= threshold:
            alert_type = "price_up" if actual_change > 0 else "price_down"
            alerts.append({
                "code": code,
                "name": stock.get("name", quote.get("name", code)),
                "alert_type": alert_type,
                "message": f"{'🚀 大涨' if actual_change > 0 else '📉 大跌'} {actual_change:+.2f}%！{stock.get('name', code)} 现价 {current_price}元",
                "price": current_price,
                "change_pct": actual_change,
                "triggered_at": now,
                "acknowledged": False,
            })

    # 保存预警
    if alerts:
        existing = load_alerts()
        existing.extend(alerts)
        # 只保留最近100条
        existing = existing[-100:]
        save_alerts(existing)

    return alerts


def check_and_notify() -> Dict:
    """
    检查预警并生成通知消息
    返回: {"new_alerts": [], "message": ""}
    """
    alerts = check_watchlist_alerts()
    if not alerts:
        return {"new_alerts": 0, "message": ""}

    # 过滤未确认的预警
    unacknowledged = [a for a in alerts if not a.get("acknowledged", False)]
    if not unacknowledged:
        return {"new_alerts": 0, "message": ""}

    # 生成通知
    message = "🔔 蛋蛋预警提醒：\n\n"
    for alert in unacknowledged[:5]:  # 最多5条
        message += f"{alert['message']}\n"

    return {
        "new_alerts": len(unacknowledged),
        "message": message,
        "alerts": unacknowledged,
    }


# ============================================================================
# 自选股管理API
# ============================================================================

def add_to_watchlist(code: str, name: str = "", base_price: float = 0, threshold: float = 5.0) -> Dict:
    """添加自选股"""
    watchlist = load_watchlist()

    # 检查是否已存在
    for stock in watchlist:
        if stock["code"] == code:
            return {"success": False, "error": "股票已在自选列表中"}

    # 获取实时价格作为参考价
    if base_price <= 0:
        quote = get_realtime_quote(code)
        if quote:
            base_price = quote.get("close", 0) or quote.get("price", 0)

    stock = {
        "code": code,
        "name": name or code,
        "base_price": base_price,
        "price_change_threshold": threshold,
        "volume_threshold": DEFAULT_VOLUME_SPIKE_THRESHOLD,
        "enabled": True,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    watchlist.append(stock)
    save_watchlist(watchlist)

    return {"success": True, "stock": stock}


def remove_from_watchlist(code: str) -> Dict:
    """删除自选股"""
    watchlist = load_watchlist()
    original_len = len(watchlist)
    watchlist = [s for s in watchlist if s["code"] != code]

    if len(watchlist) == original_len:
        return {"success": False, "error": "股票不在自选列表中"}

    save_watchlist(watchlist)
    return {"success": True, "removed": code}


def get_watchlist() -> List[Dict]:
    """获取自选股列表（带实时行情）"""
    watchlist = load_watchlist()
    if not watchlist:
        return []

    codes = [w["code"] for w in watchlist]
    quotes = get_batch_quotes(codes)

    result = []
    for stock in watchlist:
        code = stock["code"]
        quote = quotes.get(code, {})

        # 计算当前涨跌幅
        base_price = stock.get("base_price", 0)
        current_price = quote.get("price", 0)
        if base_price > 0 and current_price > 0:
            change_pct = ((current_price - base_price) / base_price) * 100
        else:
            change_pct = quote.get("change_pct", 0)

        result.append({
            **stock,
            "current_price": current_price,
            "change_pct": change_pct,
            "name": quote.get("name", stock.get("name", code)),
        })

    return result


def acknowledge_alert(code: str, triggered_at: str):
    """确认预警"""
    alerts = load_alerts()
    for alert in alerts:
        if alert["code"] == code and alert["triggered_at"] == triggered_at:
            alert["acknowledged"] = True
    save_alerts(alerts)


def clear_old_alerts():
    """清理旧预警（保留最近24小时）"""
    alerts = load_alerts()
    now = datetime.now().timestamp()
    day_ago = now - 86400  # 24小时前

    filtered = []
    for alert in alerts:
        try:
            triggered = datetime.strptime(alert["triggered_at"], "%Y-%m-%d %H:%M:%S").timestamp()
            if triggered > day_ago:
                filtered.append(alert)
        except:
            pass

    if len(filtered) < len(alerts):
        save_alerts(filtered)

    return len(alerts) - len(filtered)


# ============================================================================
# 预设自选股（方便快速添加）
# ============================================================================

PRESET_WATCHLIST = [
    {"code": "000001", "name": "平安银行", "base_price": 0},
    {"code": "600036", "name": "招商银行", "base_price": 0},
    {"code": "601318", "name": "中国平安", "base_price": 0},
    {"code": "600519", "name": "贵州茅台", "base_price": 0},
    {"code": "000858", "name": "五粮液", "base_price": 0},
    {"code": "300750", "name": "宁德时代", "base_price": 0},
]


if __name__ == "__main__":
    # 测试
    print("🥚 蛋蛋预警系统测试")
    print("=" * 40)

    # 添加测试自选股
    add_to_watchlist("600036", "招商银行")
    add_to_watchlist("601318", "中国平安")

    # 获取自选股行情
    watchlist = get_watchlist()
    print(f"\n自选股 ({len(watchlist)} 只):")
    for s in watchlist:
        print(f"  {s['name']}({s['code']}): {s.get('current_price', 0)}元 {s.get('change_pct', 0):+.2f}%")

    # 检查预警
    result = check_and_notify()
    print(f"\n预警检查: {result['new_alerts']} 条新预警")
    if result.get("message"):
        print(result["message"])
