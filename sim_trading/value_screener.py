#!/usr/bin/env python3
"""
价值投资全市场扫描器 v1.0
=========================
两步筛选法：
  Step 1: 腾讯API快速筛PE≤20的股票（几秒扫完5000+只）
  Step 2: 对候选股做深度财务分析（akshare拉财报）

运行时间：约10-15分钟（取决于Step1筛出多少只）
Cron: 每周一 09:30 触发
"""
import sys
import os
import time
import json
import requests
import logging
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "http://localhost/api"


def get_all_stock_codes():
    """获取全市场A股代码列表"""
    import akshare as ak
    # 方法1: stock_info_a_code_name（稳定快速）
    try:
        df = ak.stock_info_a_code_name()
        if df is not None and not df.empty:
            codes = df['code'].tolist()
            # 过滤ST/退市
            names = df['name'].tolist()
            valid = [(c, n) for c, n in zip(codes, names) 
                     if 'ST' not in str(n) and '退' not in str(n)]
            codes = [c for c, n in valid]
            logger.info(f"获取全市场股票: {len(codes)}只（已排除ST/退市）")
            return codes
    except Exception as e:
        logger.warning(f"stock_info_a_code_name失败: {e}")
    
    # 方法2: stock_zh_a_spot_em（备用）
    try:
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            codes = df['代码'].tolist()
            logger.info(f"获取全市场股票(备用): {len(codes)}只")
            return codes
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
    return []


def batch_get_pe_tencent(codes, batch_size=50):
    """
    Step 1: 腾讯API批量获取PE，快速筛选PE≤20的股票
    返回: [(code, name, pe, price, market_cap), ...]
    """
    candidates = []
    total = len(codes)
    
    for i in range(0, total, batch_size):
        batch_codes = codes[i:i+batch_size]
        # 转换为腾讯格式
        tencent_codes = []
        for code in batch_codes:
            code = str(code).strip()
            if len(code) != 6:
                continue
            prefix = "sh" if code.startswith(('6', '5')) else "sz"
            tencent_codes.append(f"{prefix}{code}")
        
        if not tencent_codes:
            continue
        
        query = ','.join(tencent_codes)
        try:
            r = requests.get(
                f"https://qt.gtimg.cn/q={query}",
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=10
            )
            if r.status_code != 200:
                continue
            
            items = r.text.strip().split(';')
            for item in items:
                if '="' not in item:
                    continue
                try:
                    fields = item.split('="')[1].strip('"').split('~')
                    if len(fields) < 50:
                        continue
                    
                    name = fields[1]
                    code_raw = fields[2]
                    price = float(fields[3]) if fields[3] and fields[3] != '-' else 0
                    pe = float(fields[39]) if fields[39] and fields[39] not in ('-', '0.00', '') else 0
                    market_cap = float(fields[44]) if len(fields) > 44 and fields[44] and fields[44] != '-' else 0  # 流通市值(亿)
                    
                    # 过滤条件
                    if price <= 0 or pe <= 0:
                        continue
                    # PE≤20 且 非ST/退市
                    if pe <= 20 and 'ST' not in name and '退' not in name:
                        # 排除过小市值（<30亿）和超大市值（>5000亿）
                        if market_cap > 30:
                            candidates.append({
                                'code': code_raw,
                                'name': name,
                                'pe': pe,
                                'price': price,
                                'market_cap': market_cap,
                            })
                except (IndexError, ValueError):
                    continue
        except Exception as e:
            logger.warning(f"批次{i//batch_size}请求失败: {e}")
            time.sleep(0.5)
        
        # 控制请求频率
        if i % 500 == 0 and i > 0:
            logger.info(f"  Step1进度: {i}/{total} | 已筛出{len(candidates)}只PE≤20")
            time.sleep(0.3)
    
    logger.info(f"Step1完成: {total}只 → {len(candidates)}只PE≤20")
    return candidates


def deep_analyze(code, strategy):
    """
    Step 2: 深度财务分析（单只股票）
    返回评估结果或None
    """
    try:
        result = strategy.evaluate_stock(code)
        return result
    except Exception as e:
        return {'pass': False, 'error': str(e)}


def run_value_scan(notify=True, top_n=10):
    """
    执行全市场价值扫描
    
    Args:
        notify: 是否通过lightclawbot通知结果
        top_n: 最多返回前N个候选
    
    Returns:
        list of passed stocks
    """
    from strategies.value_strategy import ValueInvestingStrategy
    
    start_time = time.time()
    logger.info("=" * 50)
    logger.info("🔍 价值投资全市场扫描启动")
    logger.info("=" * 50)
    
    # Step 1: 快速PE筛选
    logger.info("\n📊 Step 1: 腾讯API快速筛选PE≤20...")
    all_codes = get_all_stock_codes()
    if not all_codes:
        logger.error("获取股票列表失败，退出")
        return []
    
    pe_candidates = batch_get_pe_tencent(all_codes)
    logger.info(f"  PE≤20候选: {len(pe_candidates)}只")
    
    if not pe_candidates:
        logger.info("没有PE≤20的候选股，扫描结束")
        return []
    
    # Step 2: 深度财务分析
    logger.info(f"\n📊 Step 2: 深度财务分析（{len(pe_candidates)}只）...")
    strategy = ValueInvestingStrategy(strategy_id=2)
    
    passed = []
    failed_count = 0
    error_count = 0
    
    for idx, stock in enumerate(pe_candidates):
        code = stock['code']
        name = stock['name']
        
        try:
            result = deep_analyze(code, strategy)
            
            if result and result.get('pass'):
                score = result.get('score', 0)
                metrics = result.get('metrics', {})
                passed.append({
                    'code': code,
                    'name': name,
                    'score': score,
                    'pe': metrics.get('pe', stock['pe']),
                    'roe': metrics.get('roe', 0),
                    'peg': metrics.get('peg', 999),
                    'market_cap': stock['market_cap'],
                    'price': metrics.get('current_price', stock['price']),
                    'result': result,
                })
                logger.info(f"  ✅ {name}({code}) | 评分{score}/80 | PE={metrics.get('pe',0):.1f} ROE={metrics.get('roe',0):.1f}%")
            else:
                failed_count += 1
        except Exception as e:
            error_count += 1
        
        # 进度日志
        if (idx + 1) % 50 == 0:
            elapsed = time.time() - start_time
            logger.info(f"  进度: {idx+1}/{len(pe_candidates)} | 通过{len(passed)} | 耗时{elapsed:.0f}s")
        
        # akshare限流保护
        if (idx + 1) % 10 == 0:
            time.sleep(1)
        else:
            time.sleep(0.3)
    
    # 按评分排序
    passed.sort(key=lambda x: x['score'], reverse=True)
    passed = passed[:top_n]
    
    elapsed_total = time.time() - start_time
    
    # 结果汇总
    logger.info("\n" + "=" * 50)
    logger.info(f"🏁 扫描完成 | 耗时{elapsed_total/60:.1f}分钟")
    logger.info(f"   全市场: {len(all_codes)}只")
    logger.info(f"   PE≤20: {len(pe_candidates)}只")
    logger.info(f"   通过价值筛选: {len(passed)}只")
    logger.info(f"   失败/错误: {failed_count}/{error_count}")
    logger.info("=" * 50)
    
    if passed:
        logger.info("\n🎯 TOP候选股:")
        for i, s in enumerate(passed, 1):
            logger.info(f"  {i}. {s['name']}({s['code']}) | {s['score']}分 | PE={s['pe']:.1f} ROE={s['roe']:.1f}% | 市值{s['market_cap']:.0f}亿")
    
    # 通知
    if notify and passed:
        _notify_results(passed, elapsed_total, len(all_codes), len(pe_candidates))
    elif notify:
        _notify_no_result(elapsed_total, len(all_codes), len(pe_candidates))
    
    return passed


def _notify_results(passed, elapsed, total_stocks, pe_candidates_count):
    """通过lightclawbot通知扫描结果"""
    lines = [f"🔍 价值投资全市场扫描完成（{elapsed/60:.0f}分钟）\n"]
    lines.append(f"📊 {total_stocks}只 → PE≤20: {pe_candidates_count}只 → 通过: {len(passed)}只\n")
    lines.append("🎯 候选股TOP:")
    for i, s in enumerate(passed[:5], 1):
        lines.append(f"  {i}. {s['name']}({s['code']}) | {s['score']}分")
        lines.append(f"     PE={s['pe']:.1f} | ROE={s['roe']:.1f}% | 市值{s['market_cap']:.0f}亿")
    
    msg = '\n'.join(lines)
    try:
        # 通过API或直接print让cron job捕获
        print(f"\n[NOTIFY]\n{msg}")
    except Exception:
        pass


def _notify_no_result(elapsed, total_stocks, pe_candidates_count):
    """无结果通知"""
    msg = f"🔍 价值投资扫描完成（{elapsed/60:.0f}分钟）| {total_stocks}只→PE≤20:{pe_candidates_count}只→通过:0只 | 本周无符合条件标的"
    print(f"\n[NOTIFY]\n{msg}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='价值投资全市场扫描')
    parser.add_argument('--no-notify', action='store_true', help='不发送通知')
    parser.add_argument('--top', type=int, default=10, help='返回前N个候选')
    parser.add_argument('--quick', action='store_true', help='快速模式（只跑Step1）')
    args = parser.parse_args()
    
    if args.quick:
        # 快速模式：只看PE分布
        codes = get_all_stock_codes()
        candidates = batch_get_pe_tencent(codes)
        print(f"\nPE≤20候选: {len(candidates)}只")
        # 按PE排序显示前20
        candidates.sort(key=lambda x: x['pe'])
        for s in candidates[:20]:
            print(f"  {s['name']}({s['code']}) PE={s['pe']:.1f} 市值{s['market_cap']:.0f}亿")
    else:
        results = run_value_scan(notify=not args.no_notify, top_n=args.top)
