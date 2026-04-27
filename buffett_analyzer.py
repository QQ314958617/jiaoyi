"""
巴菲特价值投资分析器
=====================
评估维度：盈利能力 / 财务健康 / 估值 / 护城河 / 成长性
输出：⭐评级 + 买卖建议 + 目标价 + 止损价
"""

import requests
import numpy as np
from datetime import datetime
from functools import lru_cache
from typing import Optional

# ========== 腾讯实时行情（可靠） ==========

def get_realtime_quote(code: str) -> Optional[dict]:
    """从腾讯获取单股实时行情"""
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
            'price': float(fields[3]) if fields[3] != '-' else 0,
            'close': float(fields[4]) if fields[4] != '-' else 0,
            'open': float(fields[5]) if fields[5] != '-' else 0,
            'high': float(fields[33]) if fields[33] != '-' else 0,
            'low': float(fields[34]) if fields[34] != '-' else 0,
            'change': float(fields[31]) if fields[31] != '-' else 0,
            'change_pct': float(fields[32]) if fields[32] != '-' else 0,
            'volume': float(fields[6]) if fields[6] != '-' else 0,
            'amount': float(fields[37]) if len(fields) > 37 and fields[37] != '-' else 0,
            'time': fields[30] if len(fields) > 30 else '',
        }
    except Exception:
        return None

def get_stock_info_from_tencent(code: str) -> Optional[dict]:
    """从腾讯行情扩展字段获取PE/PB/市值"""
    try:
        if code.startswith(('6', '5')):
            q = f"sh{code}"
        else:
            q = f"sz{code}"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://gu.qq.com/'
        }
        r = requests.get(f"https://qt.gtimg.cn/q={q}", headers=headers, timeout=5)
        raw = r.text.strip()
        # 解析 v_sh600036="..." 格式
        if '"' not in raw:
            return None
        data_str = raw.split('="')[1].strip('"')
        fields = data_str.split('~')
        if len(fields) < 45:
            return None
        
        # 字段参考（腾讯行情）：
        # 3=最新价, 4=昨收, 30=时间, 31=涨跌, 32=涨跌%, 33=最高, 34=最低
        # 36=成交量(手), 37=成交额(元)
        # 39=52周最高, 40=52周最低
        # 41=市盈率, 42=股息率, 43=市净率
        # 44=总市值, 45=流通市值
        
        price = float(fields[3]) if fields[3] != '-' else 0
        pe = float(fields[41]) if len(fields) > 41 and fields[41] not in ('-', '0', '') else None
        pb = float(fields[43]) if len(fields) > 43 and fields[43] not in ('-', '0', '') else None
        total_mv = fields[44] if len(fields) > 44 else None  # 万元
        circ_mv = fields[45] if len(fields) > 45 else None
        
        # 解析市值（万元→亿元）
        total_mv_yi = float(total_mv) / 10000 if total_mv and total_mv not in ('-', '') else None
        circ_mv_yi = float(circ_mv) / 10000 if circ_mv and circ_mv not in ('-', '') else None
        
        return {
            'price': price,
            'pe': pe,
            'pb': pb,
            'total_market_cap_yi': total_mv_yi,  # 总市值（亿元）
            'circ_market_cap_yi': circ_mv_yi,     # 流通市值（亿元）
            'name': fields[1],
        }
    except Exception:
        return None


# ========== 财务数据（akshare，回调为主） ==========

def _parse_financial_row(row):
    """从财务数据行提取关键指标，自动处理%和字符串格式"""
    def _f(val):
        if val is None: return None
        s = str(val).replace('%','').strip()
        if not s or s in ('-','nan','None'): return None
        try: return float(s)
        except: return None
    return {
        'roe': _f(row.get('净资产收益率-摊薄') or row.get('净资产收益率(%)')),
        'gross_margin': _f(row.get('销售毛利率') or row.get('销售毛利率(%)')),
        'debt_ratio': _f(row.get('资产负债率') or row.get('资产负债率(%)')),
        'eps': _f(row.get('基本每股收益') or row.get('摊薄每股收益(元)')),
        'bps': _f(row.get('每股净资产') or row.get('每股净资产_调整前(元)')),
        'revenue_growth': _f(row.get('营业总收入同比增长率') or row.get('主营业务收入增长率(%)')),
        'profit_growth': _f(row.get('净利润同比增长率') or row.get('净利润增长率(%)')),
    }

def get_financial_data(code: str) -> dict:
    """
    获取财务数据（近年关键指标）
    方法1：akshare stock_financial_abstract_ths（THS，稳定）
    方法2：akshare stock_financial_analysis_indicator_em（东方财富备用）
    """
    import akshare as ak
    result = {
        'roe_latest': None, 'roe_history': [], 'gross_margin': None,
        'debt_ratio': None, 'cash_flow_ratio': None,
        'revenue_growth': None, 'profit_growth': None, 'eps': None, 'bps': None,
    }
    def _apply(p):
        # 取最新一期的值（最后一个非None值覆盖旧的）
        if p['roe'] is not None: result['roe_latest'] = p['roe']
        if p['roe'] is not None and len(result['roe_history']) < 4: result['roe_history'].append(p['roe'])
        if p['gross_margin'] is not None: result['gross_margin'] = p['gross_margin']
        if p['debt_ratio'] is not None: result['debt_ratio'] = p['debt_ratio']
        if p['eps'] is not None:
            result['eps'] = p['eps']  # 单期EPS
            if len(result.get('eps_history', [])) < 4:
                result.setdefault('eps_history', []).append(p['eps'])
        if p['bps'] is not None: result['bps'] = p['bps']
        if p['revenue_growth'] is not None: result['revenue_growth'] = p['revenue_growth']
        if p['profit_growth'] is not None: result['profit_growth'] = p['profit_growth']
    # 方法1：THS（稳定，数据全）
    for retry in range(3):
        try:
            df = ak.stock_financial_abstract_ths(symbol=code)
            if df is not None and not df.empty:
                for _, row in df.tail(4).iterrows():
                    _apply(_parse_financial_row(row))
                if result['roe_latest'] is not None: break
        except Exception:
            if retry < 2: import time; time.sleep(1); continue
            continue
    # 方法2：东方财富（备用）
    if result['roe_latest'] is None:
        for retry in range(3):
            try:
                df = ak.stock_financial_analysis_indicator_em(symbol=code)
                if df is not None and not df.empty:
                    for _, row in df.head(4).iterrows():
                        _apply(_parse_financial_row(row))
                    break
            except Exception:
                if retry < 2: import time; time.sleep(1); continue
                continue
    # 计算TTM EPS（近4季度之和，更准确反映真实PE）
    eps_hist = result.get('eps_history', [])
    if len(eps_hist) >= 4:
        result['ttm_eps'] = round(sum(eps_hist), 3)
        result['eps'] = result['ttm_eps']

    return result


def get_industry_pe() -> Optional[float]:
    """获取A股整体PE（用于参考）"""
    try:
        import akshare as ak
        df = ak.stock_industry_pe_ratio_cninfo(symbol="汽车制造业")
        if df is not None and not df.empty:
            pe_col = [c for c in df.columns if '市盈率' in c or 'PE' in c.upper()]
            if pe_col:
                val = df[pe_col[0]].iloc[-1]
                try:
                    return float(val)
                except:
                    pass
    except Exception:
        pass
    return None


# ========== 核心评估函数 ==========

def calc_buffett_score(quote: dict, financial: dict, industry_pe: float) -> dict:
    """
    巴菲特选股评分（满分100）
    各维度：PE估值 / ROE / 盈利质量 / 负债 / 现金流 / 成长性 / 毛利率 / 护城河
    """
    score = 0
    details = {}
    
    price = quote.get('price', 0)
    pe = quote.get('pe')
    pb = quote.get('pb')
    total_mv = quote.get('total_market_cap_yi')  # 亿元
    
    roe = financial.get('roe_latest')
    roe_hist = financial.get('roe_history', [])
    gross_margin = financial.get('gross_margin')
    debt_ratio = financial.get('debt_ratio')
    cf_ratio = financial.get('cash_flow_ratio')
    rev_growth = financial.get('revenue_growth')
    prof_growth = financial.get('profit_growth')
    eps = financial.get('eps')
    bps = financial.get('bps')
    
    # 1. PE估值（25分）
    # 巴菲特：PE<25 有安全边际，<15 优秀，>40 高风险
    pe_score = 0
    pe_desc = ""
    if pe and pe > 0:
        if pe < 15:
            pe_score = 25
            pe_desc = f"PE={pe:.1f} ✅ 极低估值（巴菲特标准<15）"
        elif pe < 20:
            pe_score = 22
            pe_desc = f"PE={pe:.1f} ✅ 低估值"
        elif pe < 25:
            pe_score = 18
            pe_desc = f"PE={pe:.1f} ✅ 合理（安全边际区间）"
        elif pe < 35:
            pe_score = 12
            pe_desc = f"PE={pe:.1f} ⚠️ 偏高"
        elif pe < 50:
            pe_score = 5
            pe_desc = f"PE={pe:.1f} ❌ 高估"
        else:
            pe_score = 0
            pe_desc = f"PE={pe:.1f} ❌ 极度过剩"
    else:
        pe_score = 5
        pe_desc = "PE无法获取（盈利为负或数据缺失）"
    score += pe_score
    details['pe'] = {'score': pe_score, 'max': 25, 'desc': pe_desc, 'value': pe}
    
    # 2. ROE（25分）
    # 巴菲特要求ROE>15%
    roe_score = 0
    roe_desc = ""
    if roe:
        if roe >= 20:
            roe_score = 25
            roe_desc = f"ROE={roe:.1f}% ✅ 极强（≥20%）"
        elif roe >= 15:
            roe_score = 22
            roe_desc = f"ROE={roe:.1f}% ✅ 达标（≥15%）"
        elif roe >= 12:
            roe_score = 15
            roe_desc = f"ROE={roe:.1f}% ⚠️ 尚可（12-15%）"
        elif roe >= 8:
            roe_score = 8
            roe_desc = f"ROE={roe:.1f}% ⚠️ 偏低（8-12%）"
        else:
            roe_score = 0
            roe_desc = f"ROE={roe:.1f}% ❌ 差（<8%）"
    else:
        roe_score = 3
        roe_desc = "ROE无法获取"
    score += roe_score
    details['roe'] = {'score': roe_score, 'max': 25, 'desc': roe_desc, 'value': roe, 'history': roe_hist}
    
    # 3. 负债率（15分）
    # 巴菲特要求负债率<50%
    debt_score = 0
    debt_desc = ""
    if debt_ratio is not None:
        if debt_ratio <= 30:
            debt_score = 15
            debt_desc = f"资产负债率={debt_ratio:.1f}% ✅ 极低"
        elif debt_ratio <= 50:
            debt_score = 12
            debt_desc = f"资产负债率={debt_ratio:.1f}% ✅ 达标"
        elif debt_ratio <= 60:
            debt_score = 7
            debt_desc = f"资产负债率={debt_ratio:.1f}% ⚠️ 偏高"
        else:
            debt_score = 0
            debt_desc = f"资产负债率={debt_ratio:.1f}% ❌ 过高"
    else:
        debt_score = 5
        debt_desc = "资产负债率无法获取"
    score += debt_score
    details['debt'] = {'score': debt_score, 'max': 15, 'desc': debt_desc, 'value': debt_ratio}
    
    # 4. 现金流质量（15分）
    # 经营现金流/净利润 >1.2 为优秀
    cf_score = 0
    cf_desc = ""
    if cf_ratio is not None:
        if cf_ratio >= 1.5:
            cf_score = 15
            cf_desc = f"净现比={cf_ratio:.2f} ✅ 优秀"
        elif cf_ratio >= 1.0:
            cf_score = 12
            cf_desc = f"净现比={cf_ratio:.2f} ✅ 良好"
        elif cf_ratio >= 0.8:
            cf_score = 8
            cf_desc = f"净现比={cf_ratio:.2f} ⚠️ 尚可"
        else:
            cf_score = 0
            cf_desc = f"净现比={cf_ratio:.2f} ❌ 差"
    else:
        cf_score = 5
        cf_desc = "现金流数据无法获取"
    score += cf_score
    details['cash_flow'] = {'score': cf_score, 'max': 15, 'desc': cf_desc, 'value': cf_ratio}
    
    # 5. 成长性（10分）
    growth_score = 0
    growth_desc = ""
    if rev_growth is not None and prof_growth is not None:
        avg_growth = (rev_growth + prof_growth) / 2
        if avg_growth >= 20:
            growth_score = 10
            growth_desc = f"营收+{rev_growth:.1f}%/利润+{prof_growth:.1f}% ✅ 高增长"
        elif avg_growth >= 10:
            growth_score = 8
            growth_desc = f"营收+{rev_growth:.1f}%/利润+{prof_growth:.1f}% ✅ 稳健"
        elif avg_growth >= 0:
            growth_score = 5
            growth_desc = f"营收+{rev_growth:.1f}%/利润+{prof_growth:.1f}% ⚠️ 增速放缓"
        else:
            growth_score = 0
            growth_desc = f"营收{rev_growth:.1f}%/利润{prof_growth:.1f}% ❌ 下滑"
    else:
        growth_score = 3
        growth_desc = "增速数据无法获取"
    score += growth_score
    details['growth'] = {'score': growth_score, 'max': 10, 'desc': growth_desc, 
                         'revenue_growth': rev_growth, 'profit_growth': prof_growth}
    
    # 6. 毛利率（10分）
    # 制造业毛利率>25%优秀，>15%良好，<15%差
    gm_score = 0
    gm_desc = ""
    if gross_margin is not None:
        if gross_margin >= 30:
            gm_score = 10
            gm_desc = f"毛利率={gross_margin:.1f}% ✅ 极高"
        elif gross_margin >= 20:
            gm_score = 8
            gm_desc = f"毛利率={gross_margin:.1f}% ✅ 良好"
        elif gross_margin >= 15:
            gm_score = 5
            gm_desc = f"毛利率={gross_margin:.1f}% ⚠️ 偏低"
        else:
            gm_score = 0
            gm_desc = f"毛利率={gross_margin:.1f}% ❌ 差"
    else:
        gm_score = 3
        gm_desc = "毛利率无法获取"
    score += gm_score
    details['gross_margin'] = {'score': gm_score, 'max': 10, 'desc': gm_desc, 'value': gross_margin}
    
    # 总分和评级
    max_score = 100
    pct = score / max_score * 100
    
    # 星级
    stars = int(round(score / 20))  # 5分=1星，100分=5星
    stars = max(1, min(5, stars))
    
    # 建议
    if score >= 80:
        rating = "强烈推荐"
        action = "买入"
    elif score >= 60:
        rating = "推荐"
        action = "买入/持有"
    elif score >= 40:
        rating = "中性"
        action = "观望"
    else:
        rating = "不推荐"
        action = "回避/卖出"
    
    # 目标价和止损价（基于PE回归）
    target_price = None
    stop_price = None
    if eps and eps > 0 and pe:
        # 合理PE（行业均值或25倍，取较低者）
        fair_pe = min(industry_pe or 30, 25) if (industry_pe and industry_pe > 0) else 25
        target_price = round(eps * fair_pe, 2)
        
        # 止损价：较买入价下跌-20%或PE再跌回40倍的价格（选低值）
        if price > 0:
            stop_price = round(price * 0.80, 2)  # 固定-20%
    
    return {
        'total_score': score,
        'max_score': max_score,
        'pct': round(pct, 1),
        'stars': stars,
        'rating': rating,
        'action': action,
        'target_price': target_price,
        'stop_price': stop_price,
        'details': details,
        'pe': pe,
        'pb': pb,
        'roe': roe,
        'roe_history': roe_hist,
        'gross_margin': gross_margin,
        'debt_ratio': debt_ratio,
        'cash_flow_ratio': cf_ratio,
        'revenue_growth': rev_growth,
        'profit_growth': prof_growth,
        'eps': eps,
        'bps': bps,
        'price': price,
        'total_market_cap_yi': total_mv,
        'industry_pe': industry_pe,
    }


def build_report(code: str) -> dict:
    """生成完整的巴菲特价值投资分析报告"""
    import akshare as ak
    
    # 1. 获取实时行情（腾讯）
    quote = get_stock_info_from_tencent(code)
    if not quote:
        return {'error': f'无法获取 {code} 的行情数据'}
    
    name = quote.get('name', code)
    price = quote.get('price', 0)
    
    # 2. 用 akshare stock_value_em 获取准确 PE（腾讯字段41经常错误）
    # 注意：akshare的PE(TTM)在季报披露期可能因单季度数据annualized而失真（如Q1淡季数据×4）
    # 判断方法：akshare PE > 腾讯PE × 2.5 → 说明akshare数据失真，用腾讯PE
    try:
        df_val = ak.stock_value_em(symbol=code)
        if df_val is not None and not df_val.empty:
            latest = df_val.iloc[-1]
            pe_ttm = latest.get('PE(TTM)')
            tencent_pe = quote.get('pe', 0)
            if pe_ttm and pe_ttm > 0 and pe_ttm < 200:
                # 如果akshare PE比腾讯PE高太多，说明是季报annualized失真，用腾讯PE
                if tencent_pe > 0 and pe_ttm > tencent_pe * 2.5:
                    # akshare数据失真，保持腾讯PE
                    pass
                else:
                    quote['pe'] = float(pe_ttm)
            pb = latest.get('市净率')
            if pb and pb > 0:
                quote['pb'] = float(pb)
    except Exception:
        pass
    
    # 3. 获取财务数据
    financial = get_financial_data(code)
    
    # 4. 获取行业PE
    industry_pe = get_industry_pe()
    
    # 5. 如果财务EPS为空，用PE(TTM)反推EPS（用于计算目标价，要先于calc_buffett_score）
    if not financial.get('eps') and quote.get('pe') and quote.get('price') > 0:
        if quote['pe'] < 100:
            financial['eps'] = round(quote['price'] / quote['pe'], 2)
    
    # 6. 评分（EPS此时已就绪）
    result = calc_buffett_score(quote, financial, industry_pe)
    
    # 5. 生成报告文本
    d = result['details']
    
    # 执行摘要
    summary_parts = []
    if result['stars'] >= 4:
        summary_parts.append("✅ 符合巴菲特价值投资标准")
    elif result['stars'] >= 3:
        summary_parts.append("⚠️ 部分指标达标，中性观望")
    else:
        summary_parts.append("❌ 多项指标不达标，不符合巴菲特标准")
    
    if result['pe'] and result['pe'] > 40:
        summary_parts.append(f"❌ PE={result['pe']:.1f}倍，严重高估")
    elif result['pe'] and result['pe'] < 25:
        summary_parts.append(f"✅ PE={result['pe']:.1f}倍，安全边际充足")
    
    if result['roe'] and result['roe'] < 15:
        summary_parts.append(f"❌ ROE={result['roe']:.1f}%（<15%标准）")
    elif result['roe'] and result['roe'] >= 15:
        summary_parts.append(f"✅ ROE={result['roe']:.1f}%（≥15%达标）")
    
    summary = '；'.join(summary_parts)
    
    report = {
        'code': code,
        'name': name,
        'report_date': datetime.now().strftime('%Y-%m-%d'),
        'analysis_framework': '巴菲特价值投资理念',
        'analyst': '蛋蛋AI分析助手',
        
        'current_price': price,
        'target_price': result.get('target_price'),
        'stop_price': result.get('stop_price'),
        'eps': result.get('eps'),
        'upside_pct': round((result.get('target_price', 0) - price) / price * 100, 1) if price > 0 and result.get('target_price') else None,
        
        'total_score': result['total_score'],
        'max_score': result['max_score'],
        'pct': result['pct'],
        'stars': result['stars'],
        'rating': result['rating'],
        'action': result['action'],
        'summary': summary,
        
        'indicators': {
            'PE': {
                'value': result['pe'],
                'standard': '<25倍为安全边际',
                'score': d['pe']['score'],
                'max_score': d['pe']['max'],
                'desc': d['pe']['desc'],
            },
            'ROE': {
                'value': result['roe'],
                'standard': '>15%为优秀',
                'score': d['roe']['score'],
                'max_score': d['roe']['max'],
                'desc': d['roe']['desc'],
                'history': result.get('roe_history', []),
            },
            '资产负债率': {
                'value': result['debt_ratio'],
                'standard': '<50%为健康',
                'score': d['debt']['score'],
                'max_score': d['debt']['max'],
                'desc': d['debt']['desc'],
            },
            '净现比': {
                'value': result['cash_flow_ratio'],
                'standard': '>1.2为优秀',
                'score': d['cash_flow']['score'],
                'max_score': d['cash_flow']['max'],
                'desc': d['cash_flow']['desc'],
            },
            '成长性': {
                'value': f"营收{result['revenue_growth']:.1f}%/利润{result['profit_growth']:.1f}%" if result['revenue_growth'] else None,
                'standard': '平均增速>10%为优秀',
                'score': d['growth']['score'],
                'max_score': d['growth']['max'],
                'desc': d['growth']['desc'],
            },
            '毛利率': {
                'value': result['gross_margin'],
                'standard': '>20%为良好',
                'score': d['gross_margin']['score'],
                'max_score': d['gross_margin']['max'],
                'desc': d['gross_margin']['desc'],
            },
        },
        
        'valuation': {
            'current_pe': result['pe'],
            'current_pb': result['pb'],
            'industry_pe_avg': industry_pe,
            'buffett_pe_standard': 25,
            'current_market_cap_yi': result.get('total_market_cap_yi'),
            'target_price': result.get('target_price'),
            'stop_price': result.get('stop_price'),
        },
        
        'investment_suggestion': _build_suggestion_text(result, quote, financial),
    }
    
    return report


def _build_suggestion_text(result: dict, quote: dict, financial: dict) -> str:
    """生成操作建议文本"""
    action = result['action']
    stars = result['stars']
    price = result.get('price', 0)
    target = result.get('target_price')
    stop = result.get('stop_price')
    pe = result.get('pe')
    roe = result.get('roe')
    debt = result.get('debt_ratio')
    
    lines = [
        f"📋 投资建议：{action}",
        f"⭐ 评级：{'⭐' * stars}（{result['rating']}）",
        f"📊 综合得分：{result['total_score']}/{result['max_score']}（{result['pct']}%）",
        "",
        "📌 核心依据：",
    ]
    
    # 亮点
    if pe and pe < 25:
        lines.append(f"  ✅ PE={pe:.1f}倍，安全边际内")
    if roe and roe >= 15:
        lines.append(f"  ✅ ROE={roe:.1f}%，达到巴菲特标准")
    if debt and debt < 50:
        lines.append(f"  ✅ 资产负债率={debt:.1f}%，财务健康")
    
    # 风险点
    if pe and pe >= 40:
        lines.append(f"  ❌ PE={pe:.1f}倍，严重高估")
    if roe and roe < 10:
        lines.append(f"  ❌ ROE={roe:.1f}%，盈利能力弱")
    if debt and debt >= 60:
        lines.append(f"  ❌ 资产负债率={debt:.1f}%，债务风险高")
    
    # 目标价和止损
    if target and stop:
        lines.append("")
        lines.append(f"🎯 目标价：¥{target:.2f}（基于{25}倍PE回归）")
        lines.append(f"🛡️ 止损价：¥{stop:.2f}（-20%）")
    
    return '\n'.join(lines)


def format_report_text(report: dict) -> str:
    """将报告格式化为易读文本（用于发送到聊天）"""
    if 'error' in report:
        return f"❌ {report['error']}"
    
    lines = [
        f"# 📊 {report['name']}（{report['code']}）巴菲特价值投资分析",
        f"**分析日期：** {report['report_date']}",
        f"**分析框架：** {report['analysis_framework']}",
        "",
        "---",
        "",
        "## ⭐ 投资评级",
        "",
        f"**{'⭐' * report['stars']} {report['rating']}**（{'⭐' * (5 - report['stars'])}）",
        f"**{report['action']}** | 综合得分 {report['total_score']}/{report['max_score']}（{report['pct']}%）",
        "",
        f"**{report['summary']}**",
        "",
        "---",
        "",
        "## 📈 核心指标",
        "",
    ]
    
    # 指标表格
    for name, ind in report['indicators'].items():
        val_str = f"{ind['value']:.2f}" if isinstance(ind['value'], float) else str(ind['value'] or 'N/A')
        bar = '▓' * ind['score'] + '░' * (ind['max_score'] - ind['score'])
        lines.append(f"**{name}**：{val_str} | {bar} {ind['score']}/{ind['max_score']}")
        lines.append(f"  → {ind['desc']}")
    
    lines.extend(["", "---", "", "## 💰 估值与操作建议", ""])
    
    inv = report['investment_suggestion']
    lines.append(inv)
    
    if report.get('target_price') and report.get('current_price'):
        upside = report['upside_pct']
        lines.append("")
        if upside and upside > 0:
            lines.append(f"📐 潜在涨幅：+{upside:.1f}%")
        elif upside and upside < 0:
            lines.append(f"📐 潜在涨幅：{upside:.1f}%")
    
    lines.extend(["", "---", ""])
    lines.append("*本分析仅供参考，不构成投资建议。股市有风险，投资需谨慎。*")
    
    return '\n'.join(lines)


# 简单缓存（同一个股票5分钟不重复请求财务数据）
_quote_cache = {}
_FINANCIAL_CACHE_TTL = 300  # 5分钟


def get_cached_quote(code: str) -> Optional[dict]:
    now = datetime.now().timestamp()
    if code in _quote_cache and (now - _quote_cache[code]['t']) < 30:
        return _quote_cache[code]['data']
    data = get_stock_info_from_tencent(code)
    if data:
        _quote_cache[code] = {'data': data, 't': now}
    return data


import pandas as pd  # 用于判断 NaN


# ========== 股票名称↔代码互转 ==========

def get_code_by_name(name: str) -> str:
    """根据股票名称查找代码（模糊匹配）"""
    import akshare as ak
    try:
        df = ak.stock_info_a_code_name()
        matches = df[df['name'].str.contains(name, na=False)]
        if matches.empty:
            return None
        return matches.iloc[0]['code']
    except Exception:
        return None


def search_stocks(keyword: str) -> list:
    """搜索股票（名称或代码模糊匹配）"""
    import akshare as ak
    try:
        df = ak.stock_info_a_code_name()
        mask = df['name'].str.contains(keyword, na=False) | df['code'].str.contains(keyword, na=False)
        return df[mask].head(10).to_dict('records')
    except Exception:
        return []
