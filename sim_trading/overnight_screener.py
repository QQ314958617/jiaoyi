#!/usr/bin/env python3
"""
一夜持股法选股系统 v1.0
策略：尾盘14:50-14:58选股，次日早盘卖出
原则：宁可错过，不可做错
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
import json
import sys
import os
import requests
import time

# ========== 策略参数 ==========
class Config:
    # 涨幅区间（%）
    RISE_MIN = 2.0
    RISE_MAX = 5.0
    # 成交量放大倍数
    VOLUME_RATIO_MIN = 1.5
    VOLUME_RATIO_MAX = 5.0
    # RSI 区间
    RSI_MIN = 40
    RSI_MAX = 60
    # 换手率区间（%）
    TURNOVER_MIN = 3.0
    TURNOVER_MAX = 15.0
    # 价格位置
    PRICE_ABOVE_MA5 = True
    # 单票最大仓位
    MAX_POSITION = 10000
    # 最大持仓数量
    MAX_STOCKS = 5


def log(msg):
    """简单日志"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_tencent_quote(codes):
    """从腾讯获取实时行情"""
    if not codes:
        return {}
    
    code_str = ','.join([f"sh{c}" if c.startswith(('6', '5')) else f"sz{c}" for c in codes])
    url = f"https://qt.gtimg.cn/q={code_str}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://gu.qq.com/'
        }
        r = requests.get(url, headers=headers, timeout=5)
        result = {}
        for line in r.text.strip().split('\n'):
            if '=' in line:
                key = line.split('=')[0].replace('v_', '')
                fields = line.split('="')[1].strip('"').split('~')
                if len(fields) > 10:
                    result[key.upper().replace('SH', '').replace('SZ', '')] = {
                        'name': fields[1],
                        'price': float(fields[3]) if fields[3] != '-' else 0,
                        'close': float(fields[4]) if fields[4] != '-' else 0,
                        'open': float(fields[5]) if fields[5] != '-' else 0,
                        'volume': float(fields[6]) if fields[6] != '-' else 0,
                        'amount': float(fields[37]) if len(fields) > 37 and fields[37] != '-' else 0,
                        'high': float(fields[33]) if len(fields) > 33 and fields[33] != '-' else 0,
                        'low': float(fields[34]) if len(fields) > 34 and fields[34] != '-' else 0,
                        'change': float(fields[31]) if len(fields) > 31 and fields[31] != '-' else 0,
                        'change_pct': float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0,
                        'turnover': float(fields[38]) if len(fields) > 38 and fields[38] != '-' else 0,
                        'time': fields[30] if len(fields) > 30 else '',
                    }
        return result
    except Exception as e:
        log(f"腾讯行情错误: {e}")
        return {}


def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    if len(prices) < period + 1:
        return 50.0
    
    prices = list(prices)
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_stock_history(code):
    """获取股票历史数据"""
    try:
        symbol = f"sh{code}" if code.startswith('6') else f"sz{code}"
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=(datetime.now() - pd.Timedelta(days=60)).strftime('%Y%m%d'),
            end_date=datetime.now().strftime('%Y%m%d'),
            adjust="qfq"
        )
        return df
    except Exception as e:
        log(f"获取历史数据失败 {code}: {e}")
        return pd.DataFrame()


def screen_stock(code, quote_data, hist_df):
    """
    单只股票筛选
    返回: 符合条件返回评分dict，否则返回None
    """
    try:
        name = quote_data.get('name', code)
        price = quote_data.get('price', 0)
        change_pct = quote_data.get('change_pct', 0)
        turnover = quote_data.get('turnover', 0)
        
        if price <= 0:
            return None
        
        # 1. 涨幅过滤
        if not (Config.RISE_MIN <= change_pct <= Config.RISE_MAX):
            return None
        
        # 2. 换手率过滤
        if not (Config.TURNOVER_MIN <= turnover <= Config.TURNOVER_MAX):
            return None
        
        if hist_df.empty or len(hist_df) < 5:
            return None
        
        closes = hist_df['收盘'].tolist()
        volumes = hist_df['成交量'].tolist()
        
        # 3. MA5计算
        ma5 = sum(closes[-5:]) / 5
        if price < ma5:
            return None
        
        # 4. RSI 计算
        rsi = calculate_rsi(closes)
        if not (Config.RSI_MIN <= rsi <= Config.RSI_MAX):
            return None
        
        # 5. 成交量放大倍数
        if len(volumes) >= 2:
            vol_today = volumes[-1]
            vol_yesterday = volumes[-2]
            vol_ratio = vol_today / vol_yesterday if vol_yesterday > 0 else 0
            
            if not (Config.VOLUME_RATIO_MIN <= vol_ratio <= Config.VOLUME_RATIO_MAX):
                return None
        else:
            return None
        
        # ========== 评分模型 ==========
        score = 0
        
        # 涨幅适中给高分（2-3.5%最优）
        if 2.0 <= change_pct <= 3.5:
            score += 30
        elif 3.5 < change_pct <= 5.0:
            score += 20
        
        # RSI在45-55黄金区间给高分
        if 45 <= rsi <= 55:
            score += 25
        elif 40 <= rsi < 45 or 55 < rsi <= 60:
            score += 15
        
        # 成交量放大适中给高分
        if 1.8 <= vol_ratio <= 3.0:
            score += 20
        elif 1.5 <= vol_ratio < 1.8 or 3.0 < vol_ratio <= 5.0:
            score += 10
        
        # 换手率适中给高分
        if 5.0 <= turnover <= 10.0:
            score += 15
        elif 3.0 <= turnover < 5.0 or 10.0 < turnover <= 15.0:
            score += 8
        
        # 价格强度（距离MA5越近越稳）
        ma5_distance = (price - ma5) / ma5 * 100
        if ma5_distance < 1.0:
            score += 10
        
        return {
            'code': code,
            'name': name,
            'price': price,
            'change_pct': round(change_pct, 2),
            'volume_ratio': round(vol_ratio, 2),
            'rsi': round(rsi, 1),
            'turnover': round(turnover, 2),
            'ma5': round(ma5, 2),
            'ma5_distance': round(ma5_distance, 2),
            'score': score,
            'reason': f"涨幅{change_pct:.1f}%+RSI{rsi:.0f}+放量{vol_ratio:.1f}倍"
        }
        
    except Exception as e:
        log(f"筛选失败 {code}: {e}")
        return None


def screen_overnight():
    """
    主筛选函数
    返回: 符合一夜持股法条件的股票列表（按评分排序）
    """
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    log(f"🔍 开始一夜持股法选股... 时间: {current_time}")
    
    # 获取全市场实时数据
    try:
        df = ak.stock_zh_a_spot_em()
        # 过滤ST股和问题股
        df = df[~df['名称'].str.contains('ST|退市|N', na=False)]
        df = df[df['最新价'] > 0]  # 过滤停牌股
    except Exception as e:
        log(f"获取行情数据失败: {e}")
        return []
    
    total = len(df)
    log(f"📊 候选股票总数: {total}")
    
    # 采样500只（性能考虑）
    sample_size = min(500, total)
    df_sample = df.head(sample_size)
    
    results = []
    codes_to_check = df_sample['代码'].tolist()
    
    # 批量获取实时行情
    quotes = get_tencent_quote(codes_to_check)
    
    checked = 0
    for code in codes_to_check:
        checked += 1
        
        code_str = str(code).zfill(6)
        quote = quotes.get(code_str, {})
        
        if not quote or quote.get('price', 0) <= 0:
            continue
        
        hist_df = get_stock_history(code_str)
        result = screen_stock(code_str, quote, hist_df)
        
        if result:
            results.append(result)
        
        # 避免请求过快
        time.sleep(0.05)
    
    # 按评分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 只返回前N只
    top_stocks = results[:Config.MAX_STOCKS]
    
    log(f"✅ 筛选完成: 检查{checked}只，符合条件{len(results)}只，返回前{len(top_stocks)}只")
    
    return top_stocks


def format_screening_report(results):
    """格式化筛选报告"""
    if not results:
        return "📊 **一夜持股法筛选结果**\n\n❌ 今日暂无符合条件股票\n\n⏰ 下次筛选时间: 14:50"
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        f"📊 **一夜持股法筛选结果**\n",
        f"🕐 筛选时间: {now}\n",
        f"📈 **强势股票池** (共{len(results)}只)\n\n"
    ]
    
    for i, s in enumerate(results, 1):
        lines.append(
            f"{i}. **{s['name']}({s['code']})** "
            f"现价¥{s['price']} ▲{s['change_pct']}% "
            f"RSI:{s['rsi']} 放量{s['volume_ratio']}x "
            f"换手率{s['turnover']}%\n"
            f"   评分⭐{s['score']} | {s['reason']}\n\n"
        )
    
    lines.append(f"💡 **操作建议**: 14:58前分批建仓，单票仓位¥{Config.MAX_POSITION}")
    lines.append(f"\n⚠️ 风险提示: 一夜持股法核心是次日高开获利了结，见好就收")
    
    return "".join(lines)


if __name__ == "__main__":
    print("=" * 50)
    print("🌙 一夜持股法选股系统 v1.0")
    print("=" * 50)
    
    results = screen_overnight()
    report = format_screening_report(results)
    
    print("\n" + report)
    
    if results:
        print("\n[JSON_OUTPUT]")
        print(json.dumps(results, ensure_ascii=False, indent=2))
