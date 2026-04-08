#!/usr/bin/env python3
"""
一夜持股法选股系统 v2.0 (升级版)
===============================
策略：尾盘14:30-14:58选股，次日早盘卖出
核心：宁可错过，不可做错

升级内容 v2.0:
- 涨幅调整为3%-5%（更精准）
- 加流通市值过滤（50-200亿）
- 加分时强度判断（均价线上方+强于大盘）
- 加热点板块加持
- 尾盘入场点逻辑（14:30创日内新高后回踩）
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

# ========== 策略参数 v2.0 ==========
class Config:
    # 涨幅区间（%）：3%-5%更精准（原2%-5%偏宽）
    RISE_MIN = 3.0
    RISE_MAX = 5.0
    # 成交量放大倍数
    VOLUME_RATIO_MIN = 1.5
    VOLUME_RATIO_MAX = 5.0
    # RSI 区间
    RSI_MIN = 40
    RSI_MAX = 60
    # 换手率区间（%）：5%-10%（原3%-15%偏宽）
    TURNOVER_MIN = 5.0
    TURNOVER_MAX = 10.0
    # 流通市值（亿元）：50-200亿
    MARKET_CAP_MIN = 50
    MARKET_CAP_MAX = 200
    # 价格位置：必须站上MA5
    PRICE_ABOVE_MA5 = True
    # 选股时间窗口（尾盘）：14:30-14:58（原14:50偏晚）
    SCREEN_START = "14:30"
    SCREEN_END = "14:58"
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


def get_market_cap(code):
    """获取流通市值（亿元）"""
    try:
        symbol = f"sh{code}" if code.startswith('6') else f"sz{code}"
        df = ak.stock_individual_info_em(symbol=symbol)
        for _, row in df.iterrows():
            if '流通市值' in str(row['item']):
                cap_str = str(row['value'])
                # 处理如 "198.32亿" 或 "12.56万"
                if '亿' in cap_str:
                    return float(cap_str.replace('亿', '').strip())
                elif '万' in cap_str:
                    return float(cap_str.replace('万', '').strip()) / 10000
        return None
    except:
        return None


def get_sector_hot_rank(code):
    """获取个股所在板块的热门程度"""
    try:
        # 获取个股所属行业
        symbol = f"sh{code}" if code.startswith('6') else f"sz{code}"
        df = ak.stock_individual_info_em(symbol=symbol)
        sector = None
        for _, row in df.iterrows():
            if '行业' in str(row['item']):
                sector = str(row['value'])
                break
        
        if not sector:
            return 0, None
        
        # 获取行业板块涨幅排名
        df_sector = ak.stock_board_industry_name_em()
        for _, row in df_sector.iterrows():
            if sector in str(row['板块名称']):
                change_pct = float(row['涨跌幅']) if row['涨跌幅'] != '-' else 0
                return change_pct, sector
        
        return 0, sector
    except:
        return 0, None


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


def get_index_realtime():
    """获取大盘实时指数"""
    try:
        url = "https://qt.gtimg.cn/q=sh000001"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://gu.qq.com/'}
        r = requests.get(url, headers=headers, timeout=5)
        fields = r.text.split('="')[1].strip('"').split('~')
        return {
            'price': float(fields[3]) if fields[3] != '-' else 0,
            'change_pct': float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0,
        }
    except:
        return None


def screen_stock_v2(code, quote_data, hist_df, index_data=None):
    """
    单只股票筛选 v2.0
    新增：流通市值过滤、分时强度、板块热度
    返回: 符合条件返回评分dict，否则返回None
    """
    try:
        name = quote_data.get('name', code)
        price = quote_data.get('price', 0)
        high = quote_data.get('high', 0)
        low = quote_data.get('low', 0)
        open_price = quote_data.get('open', 0)
        change_pct = quote_data.get('change_pct', 0)
        turnover = quote_data.get('turnover', 0)
        
        if price <= 0:
            return None
        
        # 1. 涨幅过滤（3%-5%更精准）
        if not (Config.RISE_MIN <= change_pct <= Config.RISE_MAX):
            return None
        
        # 2. 换手率过滤（5%-10%）
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
        
        # 6. 分时强度判断（均价线上方+强于大盘）
        if index_data:
            # 当前价格应该在今日均价上方
            today_avg_price = (high + low + price) / 3  # 简化估算
            if price < today_avg_price:
                return None
            
            # 涨幅应强于大盘
            if change_pct < index_data.get('change_pct', 0):
                return None
        
        # 7. 尾盘入场点判断（14:30后创日内新高）
        if high > 0 and price < high * 0.98:  # 价格离高点太远可能回落
            return None
        
        # 8. 流通市值过滤（可选，降低频率）
        # 注意：这个API较慢，可以在最终结果后再检查
        
        # ========== 评分模型 v2.0 ==========
        score = 0
        
        # 涨幅适中给高分（3%-4%最优）
        if 3.0 <= change_pct <= 4.0:
            score += 30
        elif 4.0 < change_pct <= 5.0:
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
        if 5.0 <= turnover <= 8.0:
            score += 15
        elif 8.0 <= turnover <= 10.0:
            score += 8
        
        # 价格强度（距离MA5越近越稳）
        ma5_distance = (price - ma5) / ma5 * 100
        if ma5_distance < 1.0:
            score += 10
        
        # 分时强度加成
        if index_data and change_pct > index_data.get('change_pct', 0):
            score += 15  # 跑赢大盘加分
        
        # 尾盘创新高加成
        if high > 0 and price >= high * 0.99:
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
            'high_of_day': high,
            'reason': f"涨幅{change_pct:.1f}%+RSI{rsi:.0f}+放量{vol_ratio:.1f}倍"
        }
        
    except Exception as e:
        log(f"筛选失败 {code}: {e}")
        return None


def filter_by_market_cap(results, top_n=20):
    """
    按流通市值过滤
    返回评分前N只股票的市值验证结果
    """
    filtered = []
    for s in results[:top_n]:
        market_cap = get_market_cap(s['code'])
        if market_cap and Config.MARKET_CAP_MIN <= market_cap <= Config.MARKET_CAP_MAX:
            s['market_cap'] = round(market_cap, 2)
            filtered.append(s)
        time.sleep(0.1)  # 避免请求过快
    
    return filtered


def screen_overnight_v2():
    """
    主筛选函数 v2.0
    返回: 符合一夜持股法条件的股票列表（按评分排序）
    """
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    log(f"🔍 一夜持股法v2.0选股... 时间: {current_time}")
    
    # 获取大盘实时数据
    index_data = get_index_realtime()
    log(f"📈 大盘状态: {'上涨' if index_data and index_data.get('change_pct', 0) > 0 else '下跌'} {index_data.get('change_pct', 0):.2f}%")
    
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
        result = screen_stock_v2(code_str, quote, hist_df, index_data)
        
        if result:
            results.append(result)
        
        # 避免请求过快
        time.sleep(0.05)
    
    # 按评分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 流通市值二次验证（前20名）
    if results:
        results = filter_by_market_cap(results, top_n=min(20, len(results)))
    
    # 只返回前N只
    top_stocks = results[:Config.MAX_STOCKS]
    
    log(f"✅ 筛选完成: 检查{checked}只，符合条件{len(results)}只，返回前{len(top_stocks)}只")
    
    return top_stocks


def format_screening_report_v2(results, index_data=None):
    """格式化筛选报告 v2.0"""
    if not results:
        return "📊 **一夜持股法v2.0筛选结果**\n\n❌ 今日暂无符合条件股票\n\n⏰ 下次筛选时间: 14:30"
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    index_info = ""
    if index_data:
        index_info = f"\n📈 大盘: {'▲' if index_data.get('change_pct', 0) > 0 else '▼'} {abs(index_data.get('change_pct', 0)):.2f}%"
    
    lines = [
        f"📊 **一夜持股法v2.0筛选结果**{index_info}\n",
        f"🕐 筛选时间: {now}\n",
        f"📈 **强势股票池** (共{len(results)}只)\n\n"
    ]
    
    for i, s in enumerate(results, 1):
        market_cap_str = f"市值{s.get('market_cap', '?')}亿" if s.get('market_cap') else ""
        lines.append(
            f"{i}. **{s['name']}({s['code']})** "
            f"现价¥{s['price']} ▲{s['change_pct']}%\n"
            f"   RSI:{s['rsi']} | 放量{s['volume_ratio']}x | "
            f"换手率{s['turnover']}% | {market_cap_str}\n"
            f"   ⭐评分{s['score']} | {s['reason']}\n\n"
        )
    
    lines.append(f"\n💡 **操作建议**: 14:30-14:58分批建仓，单票仓位¥{Config.MAX_POSITION}")
    lines.append(f"\n⚠️ 风险提示: 一夜持股法核心是次日高开获利了结，见好就收")
    lines.append(f"\n📋 **v2.0新增条件**: 涨幅3-5% | 换手率5-10% | 强于大盘 | 尾盘创新高")
    
    return "".join(lines)


if __name__ == "__main__":
    print("=" * 50)
    print("🌙 一夜持股法选股系统 v2.0 (升级版)")
    print("=" * 50)
    
    results = screen_overnight_v2()
    index_data = get_index_realtime()
    report = format_screening_report_v2(results, index_data)
    
    print("\n" + report)
    
    if results:
        print("\n[JSON_OUTPUT]")
        print(json.dumps(results, ensure_ascii=False, indent=2))
