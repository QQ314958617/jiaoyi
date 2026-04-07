"""
技术指标计算模块
包含：RSI、MACD、KDJ、布林带 等
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


def calculate_rsi(prices: list, period: int = 14) -> Optional[float]:
    """
    计算RSI指标
    RSI = 100 - (100 / (1 + RS))
    RS = 平均涨幅 / 平均跌幅
    """
    if len(prices) < period + 1:
        return None

    prices = pd.Series(prices)
    deltas = prices.diff()

    gain = deltas.where(deltas > 0, 0)
    loss = -deltas.where(deltas < 0, 0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else None


def calculate_macd(prices: list, fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict[str, float]]:
    """
    计算MACD指标
    MACD = EMA(12) - EMA(26)
    Signal = EMA(MACD, 9)
    """
    if len(prices) < slow + signal:
        return None

    prices = pd.Series(prices)

    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()

    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line

    return {
        "macd": round(float(macd.iloc[-1]), 4),
        "signal": round(float(signal_line.iloc[-1]), 4),
        "histogram": round(float(histogram.iloc[-1]), 4),
    }


def calculate_kdj(high: list, low: list, close: list, period: int = 9) -> Optional[Dict[str, float]]:
    """
    计算KDJ指标
    K = 2/3 * 前K + 1/3 * RSV
    D = 2/3 * 前D + 1/3 * K
    J = 3K - 2D
    """
    if len(close) < period:
        return None

    high = pd.Series(high)
    low = pd.Series(low)
    close = pd.Series(close)

    lowest_low = low.rolling(window=period, min_periods=period).min()
    highest_high = high.rolling(window=period, min_periods=period).max()

    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100

    k = rsv.ewm(alpha=1/3, adjust=False).mean()
    d = k.ewm(alpha=1/3, adjust=False).mean()
    j = 3 * k - 2 * d

    return {
        "k": round(float(k.iloc[-1]), 2),
        "d": round(float(d.iloc[-1]), 2),
        "j": round(float(j.iloc[-1]), 2),
    }


def calculate_bollinger(prices: list, period: int = 20, std_dev: int = 2) -> Optional[Dict[str, float]]:
    """
    计算布林带
    中轨 = MA(20)
    上轨 = 中轨 + 2*STD
    下轨 = 中轨 - 2*STD
    """
    if len(prices) < period:
        return None

    prices = pd.Series(prices)

    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()

    upper = middle + std_dev * std
    lower = middle - std_dev * std

    return {
        "upper": round(float(upper.iloc[-1]), 2),
        "middle": round(float(middle.iloc[-1]), 2),
        "lower": round(float(lower.iloc[-1]), 2),
    }


def calculate_volume_ratio(volumes: list, period: int = 5) -> Optional[float]:
    """
    计算量比（今日成交量 / 过去N日平均成交量）
    """
    if len(volumes) < period + 1:
        return None

    volumes = pd.Series(volumes)
    avg_volume = volumes.iloc[:-1].tail(period).mean()
    today_volume = volumes.iloc[-1]

    if avg_volume == 0:
        return None

    return round(float(today_volume / avg_volume), 2)


def get_stock_indicators(code: str, days: int = 30) -> Dict[str, Any]:
    """
    获取股票完整技术指标
    """
    try:
        import akshare as ak

        # 获取日线数据
        if code.startswith(('6', '5')):
            symbol = f"sh{code}"
        else:
            symbol = f"sz{code}"

        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq").tail(days + 10)

        if df.empty or len(df) < 20:
            return {"error": "数据不足"}

        close = df['收盘'].tolist()
        high = df['最高'].tolist()
        low = df['最低'].tolist()
        volume = df['成交量'].tolist()

        result = {
            "code": code,
            "close": close[-1],
            "high": high[-1],
            "low": low[-1],
            "volume": volume[-1],
        }

        # RSI
        rsi = calculate_rsi(close)
        if rsi:
            result["rsi"] = rsi

        # MACD
        macd = calculate_macd(close)
        if macd:
            result["macd"] = macd

        # KDJ
        kdj = calculate_kdj(high, low, close)
        if kdj:
            result["kdj"] = kdj

        # 布林带
        bollinger = calculate_bollinger(close)
        if bollinger:
            result["bollinger"] = bollinger

        # 量比
        vol_ratio = calculate_volume_ratio(volume)
        if vol_ratio:
            result["volume_ratio"] = vol_ratio

        return result

    except Exception as e:
        return {"error": str(e)}


# 快速判断信号
def get_signal(rsi: Optional[float], macd: Optional[Dict], kdj: Optional[Dict]) -> str:
    """
    根据技术指标给出简单信号
    返回: 超买/超卖/观望/买入/卖出
    """
    signals = []

    # RSI判断
    if rsi:
        if rsi > 70:
            signals.append("超买")
        elif rsi < 30:
            signals.append("超卖")

    # MACD判断
    if macd:
        if macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
            signals.append("MACD金叉")
        elif macd["histogram"] < 0 and macd["macd"] < macd["signal"]:
            signals.append("MACD死叉")

    # KDJ判断
    if kdj:
        if kdj["k"] < 20 and kdj["d"] < 20 and kdj["j"] < 0:
            signals.append("KDJ超卖")
        elif kdj["k"] > 80 and kdj["d"] > 80 and kdj["j"] > 100:
            signals.append("KDJ超买")

    if not signals:
        return "观望"

    # 综合判断
    if "超卖" in signals or "MACD金叉" in signals:
        return "买入信号"
    elif "超买" in signals or "MACD死叉" in signals:
        return "卖出信号"

    return "、".join(signals)
