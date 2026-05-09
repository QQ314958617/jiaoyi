#!/usr/bin/env python3
"""尾盘选股扫描 - 一夜持股法v2.3"""
import pandas as pd
import numpy as np
import akshare as ak
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🔍 尾盘选股扫描开始 - 一夜持股法v2.3")
print("=" * 60)

# 获取大盘指数数据（用于对比）
def get_index_data():
    try:
        # 沪深300
        df = ak.stock_zh_index_spot_em(symbol="000300")
        sh_comp = df[df['代码'] == '000300'].iloc[0]
        print(f"\n📊 大盘(沪深300): {sh_comp['最新价']}  涨幅: {sh_comp['涨跌幅']}%")
        return float(sh_comp['涨跌幅'])
    except Exception as e:
        print(f"获取大盘数据失败: {e}")
        return 0.0

大盘涨幅 = get_index_data()

# 获取所有A股实时数据
print("\n📥 获取A股实时数据...")
try:
    stock_df = ak.stock_zh_a_spot_em()
    print(f"共获取 {len(stock_df)} 只股票")
except Exception as e:
    print(f"获取数据失败: {e}")
    exit(1)

# 基本条件筛选
print("\n🔎 开始筛选...")

# 1. 涨幅 3%-5%
df1 = stock_df[
    (stock_df['涨跌幅'] >= 3) & 
    (stock_df['涨跌幅'] <= 5)
].copy()
print(f"① 涨幅3%-5%: {len(df1)} 只")

# 2. 换手率 3%-10%
df2 = df1[
    (df1['换手率'] >= 3) & 
    (df1['换手率'] <= 10)
].copy()
print(f"② 换手率3%-10%: {len(df2)} 只")

# 3. 流通市值 50-200亿
df3 = df2[
    (df2['流通市值'] >= 50e8) & 
    (df2['流通市值'] <= 200e8)
].copy()
print(f"③ 流通市值50-200亿: {len(df3)} 只")

# 4. 强于大盘
df4 = df3[
    (df3['涨跌幅'] > 大盘涨幅)
].copy()
print(f"④ 强于大盘({大盘涨幅}%): {len(df4)} 只")

# 需要进一步获取：成交量>1.5倍5日均量、RSI、站上分时均价线
candidates = []

for idx, row in df4.iterrows():
    try:
        code = row['代码']
        name = row['名称']
        
        # 获取日K线数据计算RSI和成交量比
        hist = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                   start_date="20260501", end_date="20260508", adjust="qfq")
        if len(hist) < 6:
            continue
        
        close_prices = hist['收盘'].values
        volumes = hist['成交量'].values
        
        # 计算RSI(14)
        delta = np.diff(close_prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = np.mean(gain[-14:]) if len(gain) >= 14 else np.mean(gain[-len(gain):])
        avg_loss = np.mean(loss[-14:]) if len(loss) >= 14 else np.mean(loss[-len(loss):])
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # RSI条件 40-65
        if not (40 <= rsi <= 65):
            continue
        
        # 成交量 > 1.5倍5日均量
        vol_5avg = np.mean(volumes[-5:])
        today_vol = volumes[-1]
        if today_vol < 1.5 * vol_5avg:
            continue
        
        # 计算评分（综合考量）
        score = (row['涨跌幅'] - 3) / 2 * 20 + (row['换手率'] - 3) / 7 * 20 + (rsi - 40) / 25 * 20
        # 附加：流通市值越接近100亿越好
        mkt_cap = row['流通市值'] / 1e8
        score += max(0, 20 - abs(mkt_cap - 100) / 5)
        
        candidates.append({
            'name': name,
            'code': code,
            '涨幅': row['涨跌幅'],
            '换手率': row['换手率'],
            'RSI': round(rsi, 1),
            '流通市值': f"{mkt_cap:.0f}亿",
            '行业': '查询中',
            'score': round(score, 1)
        })
        
        print(f"  ✓ {name}({code}) 涨幅:{row['涨跌幅']}% 换手率:{row['换手率']}% RSI:{rsi:.1f}")
        
    except Exception as e:
        continue

# 获取行业信息
if candidates:
    try:
        industry_df = ak.stock_board_industry_name_em()
        industry_dict = {}
        for _, row in industry_df.iterrows():
            try:
                cons = ak.stock_board_industry_cons_em(symbol=row['板块名称'])
                for _, s in cons.iterrows():
                    industry_dict[s['代码']] = row['板块名称']
            except:
                pass
        
        for c in candidates:
            if c['code'] in industry_dict:
                c['行业'] = industry_dict[c['code']]
    except:
        pass

# 排序并输出结果
if candidates:
    candidates.sort(key=lambda x: x['score'], reverse=True)
    print("\n" + "=" * 60)
    print("✅ 符合条件股票:")
    for i, c in enumerate(candidates[:5], 1):
        print(f"{i}. {c['name']}({c['code']}) | 涨幅:{c['涨幅']}% | 换手率:{c['换手率']}% | RSI:{c['RSI']} | {c['行业']} | 评分:{c['score']}")
else:
    print("\n" + "=" * 60)
    print("📋 今日无符合一夜持股法条件的个股")
