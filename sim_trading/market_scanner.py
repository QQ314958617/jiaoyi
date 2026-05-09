"""
全市场扫盘器 v1.0
==================
绕过东方财富IP封禁，改用腾讯行情API批量查询+akshare股票列表
实现全市场实时扫描，支持多条件过滤

架构：
1. stock_info_a_code_name → 获取全市场股票代码
2. 腾讯qt.gtimg.cn批量查询 → 获取实时价/涨幅/换手率/成交量
3. 本地过滤 → 按条件筛选
4. 补充分析 → RSI计算/分时均价线/行业信息
"""
import akshare as ak
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timezone, timedelta
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed


# ═══════════════════════════════════════
# 股票列表
# ═══════════════════════════════════════

@lru_cache(maxsize=1)
def get_all_stocks() -> pd.DataFrame:
    """获取全市场A股列表（缓存1天）"""
    df = ak.stock_info_a_code_name()
    # 只保留沪深主板+创业板+科创板
    df = df[df['code'].str.match(r'^(0\d{5}|3\d{5}|6\d{5})$')].reset_index(drop=True)
    return df


# ═══════════════════════════════════════
# 腾讯批量行情
# ═══════════════════════════════════════

def _batch_tencent_quotes(codes: list) -> dict:
    """批量查询腾讯行情"""
    if not codes:
        return {}
    
    # 添加上海/深圳前缀
    prefixed = []
    for c in codes:
        if c.startswith(('6', '5')):
            prefixed.append(f"sh{c}")
        else:
            prefixed.append(f"sz{c}")
    
    try:
        url = f"https://qt.gtimg.cn/q={','.join(prefixed)}"
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://gu.qq.com/'}
        r = requests.get(url, headers=headers, timeout=15)
        
        result = {}
        lines = r.text.strip().split(';')
        for line in lines:
            if '="' not in line:
                continue
            try:
                fields = line.split('="')[1].strip('"').split('~')
                if len(fields) < 46:
                    continue
                code_raw = fields[2]  # 纯代码
                
                # 腾讯各字段索引
                result[code_raw] = {
                    'name': fields[1],
                    'code': code_raw,
                    'open': float(fields[5]) if fields[5] != '-' else 0,
                    'close': float(fields[4]) if fields[4] != '-' else 0,  # 昨收
                    'price': float(fields[3]) if fields[3] != '-' else 0,
                    'high': float(fields[33]) if fields[33] != '-' else 0,
                    'low': float(fields[34]) if fields[34] != '-' else 0,
                    'volume': float(fields[6]) if fields[6] != '-' else 0,  # 手
                    'amount': float(fields[37]) if len(fields) > 37 and fields[37] != '-' else 0,  # 万
                    'change_pct': float(fields[32]) if len(fields) > 32 and fields[32] != '-' else 0,
                    'turnover': float(fields[38]) if len(fields) > 38 and fields[38] != '-' else 0,  # 换手率%
                    'volume_ratio': float(fields[39]) if len(fields) > 39 and fields[39] != '-' else 1.0,
                    'pe': float(fields[39]) if len(fields) > 39 and fields[39] != '-' else 0,
                    'amplitude': float(fields[43]) if len(fields) > 43 and fields[43] != '-' else 0,
                    'circulate_mv': float(fields[44]) if len(fields) > 44 and fields[44] != '-' else 0,  # 流通市值
                    'total_mv': float(fields[45]) if len(fields) > 45 and fields[45] != '-' else 0,
                    'dividend_yield': float(fields[42]) if len(fields) > 42 and fields[42] != '-' else None,
                }
            except (IndexError, ValueError):
                continue
        return result
    except Exception as e:
        return {}


def scan_market(batch_size: int = 300) -> pd.DataFrame:
    """
    全市场扫描
    返回DataFrame，包含所有股票的实时行情
    """
    stocks = get_all_stocks()
    codes = stocks['code'].tolist()
    total = len(codes)
    
    print(f"全市场扫描: {total}只股票")
    all_quotes = {}
    
    # 分批查询
    for i in range(0, total, batch_size):
        batch = codes[i:i+batch_size]
        quotes = _batch_tencent_quotes(batch)
        all_quotes.update(quotes)
        print(f"  已扫描 {min(i+batch_size, total)}/{total}，本批获取{len(quotes)}只")
        if i + batch_size < total:
            time.sleep(0.3)  # 限流保护
    
    # 组装DataFrame
    rows = []
    for code, q in all_quotes.items():
        if q['price'] > 0:  # 只包含有行情的
            rows.append(q)
    
    df = pd.DataFrame(rows)
    print(f"  有效行情: {len(df)}只")
    return df


# ═══════════════════════════════════════
# RSI计算（从K线）
# ═══════════════════════════════════════

def calc_rsi_from_kline(code: str, period: int = 14) -> float:
    """从akshare获取K线计算RSI"""
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        if df is None or df.empty or len(df) < period + 1:
            return 50.0
        closes = df['收盘'].values[-period-1:]
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 1)
    except:
        return 50.0


# ═══════════════════════════════════════
# 选股过滤
# ═══════════════════════════════════════

def filter_overnight_candidates(df: pd.DataFrame, config: dict = None) -> pd.DataFrame:
    """
    按一夜持股法条件过滤
    条件：涨幅3-5%、换手率3-10%、流通市值50-200亿、量比>1.5
    """
    cfg = config or {
        'rise_min': 3.0, 'rise_max': 5.0,
        'turnover_min': 3.0, 'turnover_max': 10.0,
        'mv_min': 50, 'mv_max': 200,
        'vol_ratio_min': 1.5,
    }
    
    filtered = df.copy()
    
    # 涨幅过滤
    if 'change_pct' in filtered.columns:
        filtered = filtered[
            (filtered['change_pct'] >= cfg['rise_min']) &
            (filtered['change_pct'] <= cfg['rise_max'])
        ]
    
    # 换手率过滤
    if 'turnover' in filtered.columns:
        filtered = filtered[
            (filtered['turnover'] >= cfg['turnover_min']) &
            (filtered['turnover'] <= cfg['turnover_max'])
        ]
    
    # 流通市值过滤（腾讯返回的是万元，需转为亿元）
    if 'circulate_mv' in filtered.columns:
        filtered['circulate_mv_yi'] = filtered['circulate_mv'] / 10000
        filtered = filtered[
            (filtered['circulate_mv_yi'] >= cfg['mv_min']) &
            (filtered['circulate_mv_yi'] <= cfg['mv_max'])
        ]
    
    # 量比过滤
    if 'volume_ratio' in filtered.columns:
        filtered = filtered[filtered['volume_ratio'] >= cfg['vol_ratio_min']]
    
    # 价格>0
    filtered = filtered[filtered['price'] > 0]
    
    return filtered.sort_values('change_pct', ascending=False)


def get_market_overview() -> dict:
    """
    市场概况
    返回涨跌分布、中位数涨幅等
    """
    df = scan_market()
    if df.empty:
        return {'error': '扫描失败'}
    
    result = {
        'total_stocks': len(df),
        'up_stocks': int((df['change_pct'] > 0).sum()),
        'down_stocks': int((df['change_pct'] < 0).sum()),
        'flat_stocks': int((df['change_pct'] == 0).sum()),
        'median_change': float(df['change_pct'].median()),
        'limit_up': int((df['change_pct'] >= 9.8).sum()),
        'limit_down': int((df['change_pct'] <= -9.8).sum()),
        'top_gainers': df.nlargest(5, 'change_pct')[['code', 'name', 'change_pct']].to_dict('records'),
        'top_losers': df.nsmallest(5, 'change_pct')[['code', 'name', 'change_pct']].to_dict('records'),
        'top_volume': df.nlargest(5, 'amount')[['code', 'name', 'amount']].to_dict('records'),
    }
    return result


# ═══════════════════════════════════════
# 命令行入口
# ═══════════════════════════════════════

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'overview':
        result = get_market_overview()
        print(f"全市场概况:")
        print(f"  总股票: {result['total_stocks']}")
        print(f"  上涨: {result['up_stocks']} 下跌: {result['down_stocks']}")
        print(f"  中位数涨幅: {result['median_change']:.2f}%")
        print(f"  涨停: {result['limit_up']} 跌停: {result['limit_down']}")
        print(f"  涨幅TOP5: {[(s['name'], s['change_pct']) for s in result['top_gainers']]}")
    
    elif len(sys.argv) > 1 and sys.argv[1] == 'overnight':
        df = scan_market()
        candidates = filter_overnight_candidates(df)
        print(f"\n一夜持股法候选: {len(candidates)}只")
        for _, r in candidates.iterrows():
            print(f"  {r['name']}({r['code']}) | 涨幅{r['change_pct']:.1f}% | 换手{r['turnover']:.1f}% | 量比{r['volume_ratio']:.1f}x")
    
    else:
        # 默认快速扫描+过滤
        df = scan_market()
        print(f"\n行情分布: 上涨{int((df['change_pct']>0).sum())} 下跌{int((df['change_pct']<0).sum())}")
        print(f"中位数涨幅: {df['change_pct'].median():.2f}%")
        
        # 涨幅靠前的
        top = df.nlargest(10, 'change_pct')
        print(f"\n涨幅TOP10:")
        for _, r in top.iterrows():
            mv = f"{(r.get('circulate_mv_yi', r.get('circulate_mv',0)/10000)):.0f}亿" if r.get('circulate_mv') else "-"
            print(f"  {r['name']}({r['code']}) | +{r['change_pct']:.1f}% | 换手{r['turnover']:.1f}% | 市值{mv} | 量比{r['volume_ratio']:.1f}x")
