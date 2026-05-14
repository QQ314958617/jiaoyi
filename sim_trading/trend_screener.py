#!/usr/bin/env python3
"""
趋势跟踪全市场扫描器 v1.0
=========================
两步筛选法：
  Step 1: 腾讯API快速筛强势股（涨幅1%-8%、量比≥1.3、非ST）
  Step 2: 对候选股做多因子趋势评分（动量+成交量+均线+MACD+RSI）

运行时间：约10-15分钟
Cron: 每日 10:00 触发
"""
import sys
import os
import time
import json
import requests
import logging
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "http://localhost/api"


def get_all_stock_codes():
    """获取全市场A股代码列表"""
    import akshare as ak
    try:
        df = ak.stock_info_a_code_name()
        if df is not None and not df.empty:
            valid = [(str(r['code']), str(r['name'])) for _, r in df.iterrows()
                     if 'ST' not in str(r['name']) and '退' not in str(r['name'])]
            logger.info(f"获取全市场股票: {len(valid)}只（已排除ST/退市）")
            return valid
    except Exception as e:
        logger.warning(f"stock_info_a_code_name失败: {e}")
    
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        if df is not None and not df.empty:
            codes = [(str(r['代码']), str(r['名称'])) for _, r in df.iterrows()]
            logger.info(f"获取全市场股票(备用): {len(codes)}只")
            return codes
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
    return []


def batch_filter_tencent(stock_list, batch_size=50):
    """
    Step 1: 腾讯API批量快速筛选强势股
    条件：涨幅1%-8%、量比≥1.3、换手率合理、流通市值>30亿
    返回: [{'code', 'name', 'price', 'change_pct', 'volume_ratio', 'turnover', 'market_cap'}, ...]
    """
    candidates = []
    total = len(stock_list)
    
    for i in range(0, total, batch_size):
        batch = stock_list[i:i+batch_size]
        tencent_codes = []
        for code, name in batch:
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
                    change_pct = float(fields[32]) if fields[32] and fields[32] != '-' else 0
                    turnover = float(fields[38]) if fields[38] and fields[38] not in ('-', '') else 0  # 换手率
                    volume_ratio = float(fields[49]) if len(fields) > 49 and fields[49] and fields[49] not in ('-', '') else 1.0  # 量比
                    market_cap = float(fields[44]) if len(fields) > 44 and fields[44] and fields[44] != '-' else 0  # 流通市值(亿)
                    
                    if price <= 0:
                        continue
                    
                    # 趋势筛选条件
                    if (1.0 <= change_pct <= 8.0 and      # 涨幅1%-8%（有动力但不追涨停）
                        volume_ratio >= 1.3 and            # 量比≥1.3（放量确认）
                        market_cap >= 30 and               # 流通市值>30亿
                        'ST' not in name and '退' not in name):
                        candidates.append({
                            'code': code_raw,
                            'name': name,
                            'price': price,
                            'change_pct': change_pct,
                            'volume_ratio': volume_ratio,
                            'turnover': turnover,
                            'market_cap': market_cap,
                        })
                except (IndexError, ValueError):
                    continue
        except Exception as e:
            logger.warning(f"批次{i//batch_size}请求失败: {e}")
            time.sleep(0.5)
        
        if i % 500 == 0 and i > 0:
            logger.info(f"  Step1进度: {i}/{total} | 已筛出{len(candidates)}只强势股")
            time.sleep(0.3)
    
    logger.info(f"Step1完成: {total}只 → {len(candidates)}只强势股（涨幅1-8%+放量）")
    return candidates


def deep_trend_analysis(code, strategy):
    """
    Step 2: 多因子趋势深度分析
    调用 check_trend_signal 获取多因子评分
    """
    try:
        result = strategy.check_trend_signal(code)
        # 统一接口：buy_signal → pass, total_score → score
        return {
            'pass': result.get('buy_signal', False),
            'score': result.get('total_score', 0),
            'metrics': result.get('metrics', {}),
            'score_breakdown': result.get('score_breakdown', {}),
            'reason': result.get('reason', ''),
        }
    except Exception as e:
        return {'pass': False, 'error': str(e)}


def run_trend_scan(notify=True, top_n=10):
    """
    执行全市场趋势扫描
    """
    from strategies.trend_strategy import TrendFollowingStrategy
    
    start_time = time.time()
    logger.info("=" * 50)
    logger.info("🔍 趋势跟踪全市场扫描启动")
    logger.info("=" * 50)
    
    # Step 1: 快速筛选强势股
    logger.info("\n📊 Step 1: 腾讯API快速筛选强势股...")
    all_stocks = get_all_stock_codes()
    if not all_stocks:
        logger.error("获取股票列表失败，退出")
        return []
    
    strong_candidates = batch_filter_tencent(all_stocks)
    logger.info(f"  强势股候选: {len(strong_candidates)}只")
    
    if not strong_candidates:
        logger.info("没有符合条件的强势股，扫描结束")
        if notify:
            print("\n[NOTIFY]\n🔍 趋势扫描完成 | 今日无强势股候选")
        return []
    
    # 按涨幅+量比综合排序，优先分析最强的
    strong_candidates.sort(key=lambda x: x['change_pct'] * 0.6 + x['volume_ratio'] * 0.4, reverse=True)
    # 最多分析前200只（控制时间）
    analyze_list = strong_candidates[:200]
    
    # Step 2: 多因子趋势评分
    logger.info(f"\n📊 Step 2: 多因子趋势评分（{len(analyze_list)}只）...")
    strategy = TrendFollowingStrategy(strategy_id=3)
    
    passed = []
    failed_count = 0
    error_count = 0
    
    for idx, stock in enumerate(analyze_list):
        code = stock['code']
        name = stock['name']
        
        try:
            result = deep_trend_analysis(code, strategy)
            
            if result and result.get('pass'):
                score = result.get('score', 0)
                metrics = result.get('metrics', {})
                passed.append({
                    'code': code,
                    'name': name,
                    'score': score,
                    'change_pct': stock['change_pct'],
                    'volume_ratio': stock['volume_ratio'],
                    'market_cap': stock['market_cap'],
                    'price': stock['price'],
                    'rsi': metrics.get('rsi', 0),
                    'ma_trend': metrics.get('ma_trend', ''),
                    'result': result,
                })
                logger.info(f"  ✅ {name}({code}) | 评分{score} | 涨{stock['change_pct']:.1f}% 量比{stock['volume_ratio']:.1f}")
            else:
                failed_count += 1
        except Exception as e:
            error_count += 1
        
        # 进度日志
        if (idx + 1) % 50 == 0:
            elapsed = time.time() - start_time
            logger.info(f"  进度: {idx+1}/{len(analyze_list)} | 通过{len(passed)} | 耗时{elapsed:.0f}s")
        
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
    logger.info(f"   全市场: {len(all_stocks)}只")
    logger.info(f"   强势股: {len(strong_candidates)}只")
    logger.info(f"   深度分析: {len(analyze_list)}只")
    logger.info(f"   通过趋势筛选: {len(passed)}只")
    logger.info("=" * 50)
    
    if passed:
        logger.info("\n🎯 TOP候选股:")
        for i, s in enumerate(passed, 1):
            logger.info(f"  {i}. {s['name']}({s['code']}) | {s['score']}分 | 涨{s['change_pct']:.1f}% 量比{s['volume_ratio']:.1f} | 市值{s['market_cap']:.0f}亿")
    
    # 通知
    if notify and passed:
        _notify_results(passed, elapsed_total, len(all_stocks), len(strong_candidates))
    elif notify:
        _notify_no_result(elapsed_total, len(all_stocks), len(strong_candidates))
    
    return passed


def _notify_results(passed, elapsed, total_stocks, strong_count):
    """通知扫描结果"""
    lines = [f"🔍 趋势跟踪全市场扫描完成（{elapsed/60:.0f}分钟）\n"]
    lines.append(f"📊 {total_stocks}只 → 强势股: {strong_count}只 → 通过: {len(passed)}只\n")
    lines.append("🎯 候选股TOP:")
    for i, s in enumerate(passed[:5], 1):
        lines.append(f"  {i}. {s['name']}({s['code']}) | {s['score']}分")
        lines.append(f"     涨{s['change_pct']:.1f}% | 量比{s['volume_ratio']:.1f} | 市值{s['market_cap']:.0f}亿")
    
    msg = '\n'.join(lines)
    print(f"\n[NOTIFY]\n{msg}")


def _notify_no_result(elapsed, total_stocks, strong_count):
    """无结果通知"""
    msg = f"🔍 趋势扫描完成（{elapsed/60:.0f}分钟）| {total_stocks}只→强势:{strong_count}只→通过:0只 | 今日无趋势信号"
    print(f"\n[NOTIFY]\n{msg}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='趋势跟踪全市场扫描')
    parser.add_argument('--no-notify', action='store_true', help='不发送通知')
    parser.add_argument('--top', type=int, default=10, help='返回前N个候选')
    parser.add_argument('--quick', action='store_true', help='快速模式（只跑Step1）')
    args = parser.parse_args()
    
    if args.quick:
        stocks = get_all_stock_codes()
        candidates = batch_filter_tencent(stocks)
        print(f"\n强势股候选: {len(candidates)}只")
        candidates.sort(key=lambda x: x['change_pct'], reverse=True)
        for s in candidates[:20]:
            print(f"  {s['name']}({s['code']}) 涨{s['change_pct']:.1f}% 量比{s['volume_ratio']:.1f} 市值{s['market_cap']:.0f}亿")
    else:
        results = run_trend_scan(notify=not args.no_notify, top_n=args.top)
