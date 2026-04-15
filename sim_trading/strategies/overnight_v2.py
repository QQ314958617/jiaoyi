"""
一夜持股法 v2.0 - rqalpha 回测策略
===================================
使用 rqalpha 日频回测框架
买入：当日收盘价（模拟14:55尾盘买入）
卖出：次日开盘价（模拟09:25集合竞价卖出）

注意：日频回测无法完全模拟盘中冲高，
用次日(最高+开盘)/2作为卖出价近似
"""

import numpy as np
from rqalpha.api import *

# ========== 策略参数 ==========
CONFIG = {
    'rise_min': 3.0,         # 最小涨幅 %
    'rise_max': 5.0,         # 最大涨幅 %
    'rsi_min': 40,           # RSI下限
    'rsi_max': 65,           # RSI上限
    'turnover_min': 3.0,     # 换手率下限 %
    'turnover_max': 10.0,    # 换手率上限 %
    'volume_ratio_min': 1.5, # 成交量放大倍数
    'market_cap_min': 50e8,  # 流通市值下限（元）
    'market_cap_max': 200e8, # 流通市值上限（元）
    'stop_loss': -3.0,       # 止损 %
    'take_profit': 3.0,      # 止盈 %
    'max_position_value': 50000,  # 单笔最大金额
    'benchmark': '000300.XSHG',   # 沪深300作为基准
}


def calculate_rsi(prices, period=14):
    """计算RSI指标"""
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


def meets_buy_criteria(stock, bar_dict, context):
    """
    检查个股是否满足一夜持股法买入条件
    返回: (bool, str) - 是否满足, 理由
    """
    bar = bar_dict[stock]
    
    # 基本检查
    if bar.isnan or bar.close <= 0:
        return False, "无数据"
    
    # 获取历史数据用于计算指标
    history = history_bars(stock, 60, '1d', ['close', 'volume', 'high', 'low', 'total_turnover'])
    if history is None or len(history) < 20:
        return False, "历史数据不足"
    
    closes = history['close']
    volumes = history['volume']
    
    # 1. 涨幅检查（当日收盘 vs 前一日收盘）
    if len(closes) < 2:
        return False, "数据不足"
    change_pct = (closes[-1] - closes[-2]) / closes[-2] * 100
    if not (CONFIG['rise_min'] <= change_pct <= CONFIG['rise_max']):
        return False, f"涨幅{change_pct:.1f}%不符合"
    
    # 2. 成交量放大
    if len(volumes) >= 6:
        avg_vol_5 = np.mean(volumes[-6:-1])  # 前5日均量（不含当日）
        vol_ratio = volumes[-1] / avg_vol_5 if avg_vol_5 > 0 else 0
        if vol_ratio < CONFIG['volume_ratio_min']:
            return False, f"量比{vol_ratio:.1f}不足"
    else:
        return False, "成交量数据不足"
    
    # 3. RSI
    rsi = calculate_rsi(closes)
    if not (CONFIG['rsi_min'] <= rsi <= CONFIG['rsi_max']):
        return False, f"RSI{rsi:.0f}超范围"
    
    # 4. 换手率
    # rqalpha日频数据中没有直接的换手率，用成交量近似
    # 用当日成交额/总市值近似换手率
    if hasattr(bar, 'total_turnover') and bar.total_turnover > 0:
        # 通过 history_bars 的 total_turnover 字段
        turnovers = history['total_turnover']
        if len(turnovers) >= 2:
            turnover_rate = turnovers[-1] / turnovers[-1] if turnovers[-1] > 0 else 0
            # 换手率在rqalpha中不直接可用，跳过此检查
            pass
    
    # 5. 价格位置 - 站上MA5
    ma5 = np.mean(closes[-5:])
    if closes[-1] < ma5:
        return False, f"未站上MA5"
    
    # 6. 强于大盘 - 个股涨幅 vs 沪深300涨幅
    benchmark_bar = bar_dict[CONFIG['benchmark']]
    if not benchmark_bar.isnan and len(closes) >= 2:
        bench_history = history_bars(CONFIG['benchmark'], 5, '1d', ['close'])
        if bench_history is not None and len(bench_history) >= 2:
            bench_change = (bench_history['close'][-1] - bench_history['close'][-2]) / bench_history['close'][-2] * 100
            if change_pct <= bench_change:
                return False, f"弱于大盘({change_pct:.1f}% vs {bench_change:.1f}%)"
    
    # 7. 流通市值过滤
    # rqalpha中获取市值需要instrument.totalShares * price
    instrument = instruments(stock)
    if instrument:
        market_cap = instrument.total_shares * closes[-1] if instrument.total_shares > 0 else 0
        if market_cap > 0:
            if not (CONFIG['market_cap_min'] <= market_cap <= CONFIG['market_cap_max']):
                return False, f"市值{market_cap/1e8:.0f}亿超范围"
    
    return True, f"涨幅{change_pct:.1f}%+RSI{rsi:.0f}+量比{vol_ratio:.1f}"


def init(context):
    """策略初始化"""
    context.stocks = []           # 候选股票池
    context.holding = None        # 当前持仓股票代码
    context.buy_date = None       # 买入日期
    context.buy_price = 0         # 买入价格
    context.trade_count = 0       # 交易次数
    context.win_count = 0         # 盈利次数
    context.total_profit = 0      # 累计盈亏
    
    logger.info("=" * 50)
    logger.info("🥚 一夜持股法 v2.0 回测启动")
    logger.info(f"   初始资金: ¥{context.portfolio.starting_cash:,.0f}")
    logger.info(f"   回测区间: {context.config.base.start_date} ~ {context.config.base.end_date}")
    logger.info("=" * 50)


def handle_bar(context, bar_dict):
    """每日盘中处理"""
    today = context.now.date()
    
    # ========== 卖出逻辑 ==========
    # 持有次日卖出（T+1：买入后下一个交易日才能卖）
    if context.holding:
        # 检查是否已持有至少1天
        if context.buy_date and today > context.buy_date:
            stock = context.holding
            bar = bar_dict[stock]
            
            if not bar.isnan and bar.close > 0:
                # 计算收益
                # 使用次日开盘价近似"早盘冲高卖出"
                # rqalpha的order以收盘价成交（日频限制）
                # 用 (最高+开盘)/2 近似早盘卖出价
                sell_price_approx = (bar.high + bar.open) / 2 if bar.high > 0 else bar.close
                profit_pct = (sell_price_approx - context.buy_price) / context.buy_price * 100
                
                # 止损检查
                close_profit_pct = (bar.close - context.buy_price) / context.buy_price * 100
                
                if close_profit_pct <= CONFIG['stop_loss']:
                    # 触发止损 - 以收盘价卖出
                    order_target_value(stock, 0)
                    logger.info(f"🔴 止损卖出 {stock} | 买入¥{context.buy_price:.2f} → 卖出¥{bar.close:.2f} | 亏损{close_profit_pct:.1f}%")
                    context.trade_count += 1
                    context.total_profit += close_profit_pct
                    context.holding = None
                    context.buy_date = None
                    context.buy_price = 0
                elif profit_pct >= CONFIG['take_profit']:
                    # 冲高止盈
                    order_target_value(stock, 0)
                    logger.info(f"🟢 止盈卖出 {stock} | 买入¥{context.buy_price:.2f} → 卖出¥{bar.close:.2f} | 盈利{close_profit_pct:.1f}%")
                    context.trade_count += 1
                    context.win_count += 1
                    context.total_profit += close_profit_pct
                    context.holding = None
                    context.buy_date = None
                    context.buy_price = 0
                else:
                    # 次日无明确信号，强制卖出（一夜持股法：不管涨跌次日都要走）
                    order_target_value(stock, 0)
                    is_win = close_profit_pct > 0
                    emoji = "🟢" if is_win else "🔴"
                    logger.info(f"{emoji} 次日卖出 {stock} | 买入¥{context.buy_price:.2f} → 卖出¥{bar.close:.2f} | {'盈利' if is_win else '亏损'}{close_profit_pct:.1f}%")
                    context.trade_count += 1
                    if is_win:
                        context.win_count += 1
                    context.total_profit += close_profit_pct
                    context.holding = None
                    context.buy_date = None
                    context.buy_price = 0
    
    # ========== 买入逻辑 ==========
    # 只有空仓时才能买入
    if context.holding:
        return
    
    # 遍历候选股票池，找符合条件的
    # 为了性能，先从沪深300成分股中选
    for stock in context.run_info.stock_list[:300]:
        if stock == CONFIG['benchmark']:
            continue
        
        ok, reason = meets_buy_criteria(stock, bar_dict, context)
        if ok:
            bar = bar_dict[stock]
            # 买入
            buy_value = min(CONFIG['max_position_value'], context.portfolio.cash * 0.95)
            if buy_value > bar.close * 100:  # 至少买得起1手
                shares = int(buy_value / (bar.close * 100)) * 100  # 按手取整
                if shares > 0:
                    order_shares(stock, shares)
                    context.holding = stock
                    context.buy_date = today
                    context.buy_price = bar.close
                    logger.info(f"🔵 买入 {stock} | ¥{bar.close:.2f} x {shares}股 | {reason}")
                    break  # 一天只买一只


def after_trading(context):
    """盘后处理"""
    if context.trade_count > 0:
        win_rate = context.win_count / context.trade_count * 100
        logger.info(f"📊 累计: {context.trade_count}笔 | 胜率{win_rate:.1f}% | 累计收益{context.total_profit:.1f}%")


def after_strategy(context):
    """策略结束"""
    if context.trade_count > 0:
        win_rate = context.win_count / context.trade_count * 100
        avg_profit = context.total_profit / context.trade_count
        logger.info("=" * 50)
        logger.info(f"📊 回测完成")
        logger.info(f"   总交易: {context.trade_count}笔")
        logger.info(f"   胜率: {win_rate:.1f}% ({context.win_count}胜/{context.trade_count - context.win_count}负)")
        logger.info(f"   平均收益: {avg_profit:.2f}%")
        logger.info(f"   累计收益: {context.total_profit:.1f}%")
        logger.info("=" * 50)
