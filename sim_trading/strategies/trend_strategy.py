"""
趋势跟踪策略模块
================
强势股趋势波段策略
信号：20日均线金叉60日、放量突破前高、MACD金叉
持股1-2周，沿5日线持有
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies import BaseStrategy, StrategyRegistry
from datetime import datetime, timezone, timedelta, time as t_time
import akshare as ak
import pandas as pd
import numpy as np
import requests


class TrendFollowingStrategy(BaseStrategy):
    """趋势跟踪策略"""
    
    name = "趋势跟踪"
    strategy_type = "trend"
    description = "强势股趋势波段，均线金叉+放量突破，持股1-2周"
    
    def __init__(self, strategy_id: int, config: dict = None):
        super().__init__(strategy_id, config)
        self.config = {
            'ma_short': 20,            # 短周期均线
            'ma_long': 60,             # 长周期均线
            'volume_ratio_min': 1.5,   # 成交量放大倍数
            'rsi_min': 40,             # RSI下限
            'rsi_max': 70,             # RSI上限
            'stop_loss': -5.0,         # 止损%
            'take_profit': 10.0,       # 止盈%
            'max_hold_days': 14,       # 最长持有天数
            ** (config or {})
        }
    
    def is_trading_time(self) -> bool:
        """日内可交易时间"""
        bj = self.get_bj_time()
        now = bj.time()
        return t_time(9, 30) <= now <= t_time(15, 0)
    
    def get_tencent_quote(self, code: str) -> dict:
        """获取腾讯实时行情"""
        try:
            if code.startswith(('6', '5')):
                q = f"sh{code}"
            else:
                q = f"sz{code}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://gu.qq.com/'
            }
            r = requests.get(f"https://qt.gtimg.cn/q={q}", headers=headers, timeout=5)
            fields = r.text.split('="')[1].strip('"').split('~')
            if len(fields) < 10:
                return None
            return {
                'name': fields[1],
                'code': code,
                'price': float(fields[3]) if fields[3] else 0,
                'change_pct': float(fields[32]) if fields[32] else 0,
                'volume_ratio': float(fields[39]) if fields[39] else 1.0,
                'amount': float(fields[38]) if fields[38] else 0,
                'turnover': float(fields[38]) if fields[5] else 0,
            }
        except Exception as e:
            return None
    
    def get_kline_data(self, code: str, days: int = 120) -> pd.DataFrame:
        """获取日K线数据"""
        try:
            if code.startswith(('6', '5')):
                symbol = f"sh{code}"
            else:
                symbol = f"sz{code}"
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
            if df is not None and not df.empty:
                df = df.sort_values('日期').tail(days)
                return df
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def calculate_rsi(self, prices, period=14):
        """计算RSI"""
        if len(prices) < period + 1:
            return 50.0
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def check_trend_signal(self, code: str) -> dict:
        """
        检查趋势信号
        返回: {buy_signal, reason, strength, ...}
        """
        # 获取K线数据
        df = self.get_kline_data(code)
        if df.empty or len(df) < 60:
            return {'buy_signal': False, 'reason': '数据不足'}
        
        closes = df['收盘'].values
        volumes = df['成交量'].values
        dates = df['日期'].values
        
        # 计算均线
        ma_short = pd.Series(closes).rolling(self.config['ma_short']).mean().values
        ma_long = pd.Series(closes).rolling(self.config['ma_long']).mean().values
        
        # 计算成交量均值
        vol_ma = pd.Series(volumes).rolling(5).mean().values
        
        # 取最新值
        latest_close = closes[-1]
        latest_ma_short = ma_short[-1]
        latest_ma_long = ma_long[-1]
        latest_vol = volumes[-1]
        latest_vol_ma = vol_ma[-1]
        
        # 信号检查
        signals = []
        strength = 0
        
        # 1. 均线金叉（20日上穿60日）
        prev_ma_short = ma_short[-2] if len(ma_short) > 1 else 0
        prev_ma_long = ma_long[-2] if len(ma_long) > 1 else 0
        if prev_ma_short <= prev_ma_long and latest_ma_short > latest_ma_long:
            signals.append('均线金叉')
            strength += 2
        elif latest_ma_short > latest_ma_long:
            # 已经多头排列
            signals.append('均线多头排列')
            strength += 1
        
        # 2. 放量突破
        if latest_vol > latest_vol_ma * self.config['volume_ratio_min']:
            signals.append('放量')
            strength += 1
        
        # 3. 收盘站上20日线
        if latest_close > latest_ma_short:
            signals.append('站上短线均线')
            strength += 1
        
        # 4. RSI不过热
        rsi = self.calculate_rsi(closes)
        if rsi < self.config['rsi_max']:
            signals.append(f'RSI={rsi:.0f}')
        if rsi < self.config['rsi_min']:
            signals.append('RSI偏低')
        
        # 5. 价格突破前高（最近30天最高点）
        recent_high = np.max(closes[-30:])
        if latest_close >= recent_high * 0.98:
            signals.append('接近阶段新高')
            strength += 1
        
        # 获取实时行情
        quote = self.get_tencent_quote(code)
        current_price = quote['price'] if quote else latest_close
        
        total_signals = len(signals)
        buy_signal = total_signals >= 3 and strength >= 3 and rsi < self.config['rsi_max']
        
        return {
            'buy_signal': buy_signal,
            'reason': '；'.join(signals) if signals else '无有效信号',
            'strength': strength,
            'signal_count': total_signals,
            'current_price': float(current_price),
            'ma_short': float(latest_ma_short),
            'ma_long': float(latest_ma_long),
            'rsi': float(rsi),
            'volume_ratio': float(latest_vol / latest_vol_ma) if latest_vol_ma > 0 else 1.0,
        }
    
    def should_sell(self, cost_price: float, current_price: float, highest_since_buy: float, hold_days: int) -> tuple:
        """
        判断是否该卖出
        返回: (should_sell, reason)
        """
        cfg = self.config
        
        profit_pct = (current_price - cost_price) / cost_price * 100
        peak_to_now = (current_price - highest_since_buy) / highest_since_buy * 100 if highest_since_buy > 0 else 0
        
        # 止损
        if profit_pct <= -cfg['stop_loss']:
            return True, f"止损触发：亏损{profit_pct:.1f}%（≤{cfg['stop_loss']}%）"
        
        # 止盈
        if profit_pct >= cfg['take_profit']:
            return True, f"止盈触发：盈利{profit_pct:.1f}%（≥{cfg['take_profit']}%）"
        
        # 从最高点回落
        if peak_to_now <= -3.0:
            return True, f"高位回落{peak_to_now:.1f}%，锁定利润"
        
        # 超过最长持有天数
        if hold_days >= cfg['max_hold_days']:
            return True, f"超时卖出：已持有{hold_days}天（上限{cfg['max_hold_days']}天）"
        
        return False, ""


# 注册策略
StrategyRegistry.register(TrendFollowingStrategy)
