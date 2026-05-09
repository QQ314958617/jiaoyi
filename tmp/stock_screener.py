#!/usr/bin/env python3
"""
一夜持股法v2.3 尾盘选股扫描
条件：涨幅3-5%, 成交量>1.5倍5日均量, 换手率3-10%, 流通市值50-200亿, RSI 40-65, 站上分时均价线, 强于大盘
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============ 1. 获取大盘数据 ============
def get_market_index():
    """获取沪深300指数当前涨幅"""
    try:
        df = ak.stock_zh_index_spot_em(symbol="沪深300")
        hs300 = df[df['代码'] == '000300'] if '000300' in df['代码'].values else None
        if hs300 is not None and len(hs300) > 0:
            change = float(hs300['涨跌幅'].values[0])
            return change
    except:
        pass
    
    # 备选：获取上证指数
    try:
        df = ak.stock_zh_index_spot_em(symbol="上证指数")
        if len(df) > 0:
            change = float(df['涨跌幅'].values[0])
            return change
    except:
        pass
    return 0.0

# ============ 2. 获取所有A股实时数据 ============
def get_realtime_quotes():
    """获取A股实时行情"""
    try:
        df = ak.stock_zh_a_spot_em()
        return df
    except Exception as e:
        print(f"获取实时行情失败: {e}")
        return None

# ============ 3. 计算RSI ============
def calculate_rsi(close_prices, period=14):
    """计算RSI"""
    if len(close_prices) < period + 1:
        return None
    
    delta = np.diff(close_prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ============ 4. 获取分时均价线 ============
def get_intraday_avg_price(code):
    """获取分时均价（简化为当日均价估算）"""
    try:
        today = datetime.now().strftime('%Y%m%d')
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=today, end_date=today, adjust="qfq")
        if len(df) > 0:
            # 用当日均价估算分时均价线
            return (df['开盘'].values[0] + df['收盘'].values[0] + df['最高'].values[0] + df['最低'].values[0]) / 4
    except:
        pass
    return None

# ============ 5. 主扫描逻辑 ============
def screen_stocks():
    print("="*60)
    print("🔍 一夜持股法v2.3 尾盘选股扫描")
    print("="*60)
    
    # 获取大盘涨幅
    market_change = get_market_index()
    print(f"\n📊 大盘（沪深300/上证）涨幅: {market_change:.2f}%")
    
    # 获取实时行情
    print("\n📡 获取A股实时行情数据...")
    df = get_realtime_quotes()
    
    if df is None or len(df) == 0:
        print("❌ 获取行情数据失败")
        return []
    
    # 筛选条件
    # 涨幅: 3%-5%
    # 换手率: 3%-10%
    # 流通市值: 50-200亿
    
    print(f"原始股票数量: {len(df)}")
    
    # 过滤ST
    if '名称' in df.columns:
        df = df[~df['名称'].str.contains('ST|退市', na=False)]
    
    # 基础条件筛选
    candidates = []
    
    for idx, row in df.iterrows():
        try:
            # 解析数据
            name = str(row.get('名称', ''))
            code = str(row.get('代码', ''))
            
            # 跳过ST和空值
            if not name or name == 'nan' or 'ST' in name:
                continue
            
            # 涨幅
            change_str = str(row.get('涨跌幅', '0'))
            change = float(change_str) if change_str.replace('.', '').replace('-', '').isdigit() else 0
            
            # 换手率
            turnover_str = str(row.get('换手率', '0'))
            turnover = float(turnover_str) if turnover_str.replace('.', '').replace('-', '').isdigit() else 0
            
            # 流通市值（万元转亿元）
            mktcap_str = str(row.get('流通市值', '0'))
            try:
                mktcap = float(mktcap_str) / 10000  # 万元->亿元
            except:
                mktcap = 0
            
            # 成交量
            volume_str = str(row.get('成交量', '0'))
            try:
                volume = float(volume_str)
            except:
                volume = 0
            
            # 5日均量
            vol_5d_str = str(row.get('5日均量', '0'))
            try:
                vol_5d = float(vol_5d_str)
            except:
                vol_5d = 0
            
            # 收盘价
            price_str = str(row.get('最新价', '0'))
            current_price = float(price_str) if price_str.replace('.', '').isdigit() else 0
            
            # RSI
            rsi_str = str(row.get('RSI', '0'))
            rsi = float(rsi_str) if rsi_str.replace('.', '').isdigit() else 0
            
            # 条件1: 涨幅3-5%
            if not (3.0 <= change <= 5.0):
                continue
            
            # 条件2: 换手率3-10%
            if not (3.0 <= turnover <= 10.0):
                continue
            
            # 条件3: 流通市值50-200亿
            if not (50 <= mktcap <= 200):
                continue
            
            # 条件4: RSI 40-65
            if not (40 <= rsi <= 65):
                continue
            
            # 条件5: 成交量>1.5倍5日均量
            if vol_5d > 0 and volume < vol_5d * 1.5:
                continue
            elif vol_5d == 0 and volume == 0:
                continue
            
            # 条件6: 站上分时均价线（用当前价>今日均价估算）
            today = datetime.now().strftime('%Y%m%d')
            try:
                hist = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=today, end_date=today, adjust="qfq")
                if len(hist) > 0:
                    avg_price = (hist['开盘'].values[0] + hist['收盘'].values[0] + hist['最高'].values[0] + hist['最低'].values[0]) / 4
                    if current_price < avg_price:
                        continue
                else:
                    # 无法获取今日数据，跳过此条件
                    pass
            except:
                pass
            
            # 条件7: 强于大盘
            if change <= market_change:
                continue
            
            # 行业信息
            industry = str(row.get('行业', '未知'))
            
            # 计算评分
            score = 0
            score += (change - 3) * 10  # 涨幅基础分
            score += (turnover - 3) * 5  # 换手率加分
            score += (65 - rsi) * 0.5 if rsi < 65 else 0  # RSI偏低加分（还有空间）
            score += 10 if change > market_change + 1 else 5  # 明显强于大盘加分
            
            candidates.append({
                'name': name,
                'code': code,
                'change': change,
                'turnover': turnover,
                'rsi': rsi,
                'mktcap': mktcap,
                'volume': volume,
                'vol_5d': vol_5d,
                'industry': industry,
                'score': score,
                'current_price': current_price
            })
            
        except Exception as e:
            continue
    
    # 按评分排序
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    return candidates[:10]  # 最多返回10只

# ============ 6. 输出结果 ============
if __name__ == "__main__":
    results = screen_stocks()
    
    if results:
        print(f"\n✅ 找到 {len(results)} 只符合条件的股票:\n")
        for i, stock in enumerate(results, 1):
            print(f"{i}. {stock['name']}({stock['code']}) | "
                  f"涨幅:{stock['change']:.2f}% | "
                  f"换手率:{stock['turnover']:.2f}% | "
                  f"RSI:{stock['rsi']:.1f} | "
                  f"流通市值:{stock['mktcap']:.1f}亿 | "
                  f"行业:{stock['industry']} | "
                  f"评分:{stock['score']:.1f}")
    else:
        print("\n📋 今日无符合一夜持股法条件的个股")
    
    # 保存结果供后续使用
    import json
    with open('/tmp/screened_stocks.json', 'w') as f:
        json.dump(results, f, ensure_ascii=False)
