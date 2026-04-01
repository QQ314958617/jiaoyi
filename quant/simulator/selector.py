"""
AI量化选股策略 v1.0
==================
策略思路：
1. 趋势跟踪：EMA多头排列（快线>慢线）
2. 动量筛选：近期涨幅适中（不太热不太冷）
3. 波动率过滤：波动率不能太低也不能太高
4. 成交量确认：放量上涨

选股评分标准：
- 均线多头：+30分
- RSI 40-70（健康区间）：+20分
- 近5日涨幅 3%-15%：+30分
- 成交量放大：+20分
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
import json
import os

# ============ 工具函数 ============

def get_stock_hist(stock_code, days=60):
    """获取股票历史数据"""
    try:
        # 转换代码格式
        if stock_code.startswith('6'):
            symbol = f"sh{stock_code}"
        else:
            symbol = f"sz{stock_code}"
        
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days+30)).strftime('%Y%m%d')
        
        df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                 start_date=start_date, end_date=end_date)
        df = df.tail(days)
        return df
    except Exception as e:
        return None

def calc_ema(series, n):
    """计算EMA"""
    return series.ewm(span=n, adjust=False).mean()

def calc_rsi(series, n=14):
    """计算RSI"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=n).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=n).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze_stock(stock_code, name):
    """分析单只股票，返回评分和建议"""
    df = get_stock_hist(stock_code, 60)
    if df is None or len(df) < 30:
        return None
    
    # 重命名列（akshare返回12列：日期,股票代码,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率）
    df.columns = ['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率']
    df = df.sort_values('日期')
    
    close = df['收盘'].astype(float)
    
    # 计算指标
    ema5 = calc_ema(close, 5)
    ema10 = calc_ema(close, 10)
    ema20 = calc_ema(close, 20)
    ema60 = calc_ema(close, 60)
    rsi = calc_rsi(close, 14)
    
    latest = df.iloc[-1]
    prev5 = df.iloc[-6] if len(df) >= 6 else df.iloc[0]
    prev10 = df.iloc[-11] if len(df) >= 11 else df.iloc[0]
    
    # ===== 评分逻辑 =====
    score = 0
    reasons = []
    
    # 1. 均线多头排列 (30分)
    if ema5.iloc[-1] > ema10.iloc[-1] > ema20.iloc[-1]:
        score += 30
        reasons.append("✅ 均线多头排列")
    elif ema5.iloc[-1] > ema10.iloc[-1]:
        score += 15
        reasons.append("🟡 短期均线多头")
    
    # 2. RSI健康区间 (20分)
    rsi_val = rsi.iloc[-1]
    if 40 <= rsi_val <= 70:
        score += 20
        reasons.append(f"✅ RSI={rsi_val:.1f}（健康区间）")
    elif rsi_val < 30:
        score += 10
        reasons.append(f"🟡 RSI={rsi_val:.1f}（超卖，可能反弹）")
    elif rsi_val > 70:
        score += 5
        reasons.append(f"🟡 RSI={rsi_val:.1f}（偏热）")
    
    # 3. 动量筛选 (30分) - 近5日涨幅
    gain_5d = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(df) >= 6 else 0
    if 3 <= gain_5d <= 15:
        score += 30
        reasons.append(f"✅ 近5日涨幅{gain_5d:.1f}%（适中）")
    elif 0 <= gain_5d < 3:
        score += 15
        reasons.append(f"🟡 近5日涨幅{gain_5d:.1f}%（蓄势中）")
    elif gain_5d > 15:
        score += 5
        reasons.append(f"⚠️ 近5日涨幅{gain_5d:.1f}%（过热）")
    else:
        score -= 10
        reasons.append(f"❌ 近5日下跌{gain_5d:.1f}%")
    
    # 4. 成交量放大 (20分)
    vol_avg_5 = df['成交量'].iloc[-5:].mean()
    vol_avg_20 = df['成交量'].iloc[-20:].mean()
    vol_ratio = vol_avg_5 / vol_avg_20 if vol_avg_20 > 0 else 1
    if vol_ratio > 1.5:
        score += 20
        reasons.append(f"✅ 成交量放大({vol_ratio:.2f}x)")
    elif vol_ratio > 1.0:
        score += 10
        reasons.append(f"🟡 成交量温和")
    
    # 5. 趋势确认（收盘价站上均线）
    if close.iloc[-1] > ema20.iloc[-1]:
        score += 10
        reasons.append("✅ 股价站上20日线")
    
    # ===== 交易建议 =====
    current_price = float(latest['收盘'])
    change_pct = float(latest['涨跌幅'])
    
    # 建议
    if score >= 80:
        action = "强烈买入"
    elif score >= 60:
        action = "考虑买入"
    elif score >= 40:
        action = "观望"
    else:
        action = "不参与"
    
    return {
        'code': stock_code,
        'name': name,
        'price': current_price,
        'change_pct': change_pct,
        'score': score,
        'action': action,
        'reasons': reasons,
        'ema5': round(ema5.iloc[-1], 2),
        'ema10': round(ema10.iloc[-1], 2),
        'ema20': round(ema20.iloc[-1], 2),
        'rsi': round(rsi_val, 1),
        'vol_ratio': round(vol_ratio, 2),
        'gain_5d': round(gain_5d, 2)
    }

def scan_market(top_n=20):
    """扫描市场，选出top股票"""
    print("🔍 正在扫描市场...")
    
    # 获取今日涨跌幅排行
    try:
        df = ak.stock_zh_a_spot_em()
        # 过滤ST股、涨跌停股
        df = df[df['涨跌幅'].notna()]
        df = df[~df['名称'].str.contains('ST', na=False)]
        df = df[df['涨跌幅'] > -9]  # 非跌停
        df = df[df['涨跌幅'] < 9]  # 非涨停
        
        # 按成交额排序，取前100只活跃股
        df = df.nlargest(100, '成交额')
        
        candidates = []
        for idx, row in df.iterrows():
            code = str(row['代码'])
            name = str(row['名称'])
            try:
                price = float(row['最新价'])
                change = float(row['涨跌幅'])
            except:
                continue
            candidates.append({
                'code': code,
                'name': name,
                'price': price,
                'change_pct': change
            })
        
        print(f"📊 已获取 {len(candidates)} 只候选股票，开始分析...")
        
        results = []
        for i, cand in enumerate(candidates[:top_n]):
            if (i+1) % 5 == 0:
                print(f"  分析进度: {i+1}/{min(top_n, len(candidates))}")
            
            result = analyze_stock(cand['code'], cand['name'])
            if result:
                results.append(result)
        
        # 按评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results
        
    except Exception as e:
        print(f"扫描失败: {e}")
        return []

def print_analysis(results):
    """打印分析结果"""
    print("\n" + "="*70)
    print("📈 AI选股结果".center(50))
    print("="*70)
    
    print("\n🏆 强烈买入候选（80分以上）：")
    strong_buys = [r for r in results if r['score'] >= 80]
    if strong_buys:
        for r in strong_buys[:5]:
            print(f"\n  {r['code']} {r['name']}")
            print(f"    价格: {r['price']} | 涨跌: {r['change_pct']:+.2f}%")
            print(f"    评分: {r['score']} | RSI: {r['rsi']} | 5日涨幅: {r['gain_5d']}%")
            print(f"    建议: {r['action']}")
            for reason in r['reasons']:
                print(f"    {reason}")
    else:
        print("  暂无")
    
    print("\n💡 考虑买入候选（60-79分）：")
    consider_buys = [r for r in results if 60 <= r['score'] < 80]
    if consider_buys:
        for r in consider_buys[:5]:
            print(f"  {r['code']} {r['name']} | 评分:{r['score']} | 价格:{r['price']} | {r['action']}")
    else:
        print("  暂无")
    
    return strong_buys, consider_buys

if __name__ == "__main__":
    print("="*70)
    print(f"🤖 AI量化选股系统 | 扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    results = scan_market(top_n=30)
    strong_buys, consider_buys = print_analysis(results)
    
    # 保存结果
    report = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'total_scanned': len(results),
        'strong_buys': strong_buys[:5],
        'consider_buys': consider_buys[:5]
    }
    
    os.makedirs('/root/.openclaw/workspace/quant/simulator/data', exist_ok=True)
    with open('/root/.openclaw/workspace/quant/simulator/data/daily_scan.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*70)
    print("✅ 今日扫描完成！结果已保存")
    print("="*70)
