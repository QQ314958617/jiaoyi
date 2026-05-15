"""
交易相关路由: /api/trade, /api/portfolio, /api/trades, /api/stats, /api/equity
"""
import logging
from datetime import datetime, date, timezone, timedelta
from flask import Blueprint, jsonify, request

import database as db
from services.quote import get_tencent_quote

logger = logging.getLogger(__name__)

trading_bp = Blueprint('trading', __name__)


# ========== A股市场规则 ==========

def is_market_open():
    """检查当前是否在A股交易时段 (09:30-11:30, 13:00-15:00)"""
    bj_tz = timezone(timedelta(hours=8))
    now = datetime.now(bj_tz)
    h, m = now.hour, now.minute
    if (h == 9 and m >= 30) or (h == 10) or (h == 11 and m <= 30):
        return True
    if (h == 13) or (h == 14) or (h == 15 and m == 0):
        return True
    return False


def calc_buy_commission(amount):
    """A股买入手续费: 佣金万2.5(最低5元) + 过户费万0.1 ≈ 0.026%"""
    fee = amount * 0.00026
    return max(fee, 5.0)


def calc_sell_commission(amount):
    """A股卖出手续费: 佣金万2.5(最低5元) + 过户费万0.1 + 印花税千1 ≈ 0.126%"""
    fee = amount * 0.00126
    return max(fee, 5.0)


@trading_bp.route('/api/portfolio')
def get_portfolio():
    """获取当前持仓（支持按策略过滤）"""
    strategy_id = request.args.get('strategy_id', type=int)
    account = db.get_account()
    positions = db.get_positions(strategy_id=strategy_id)
    return jsonify({
        **account,
        'positions': {p['stock_code']: p for p in positions},
        'strategy_id': strategy_id
    })


@trading_bp.route('/api/trades')
def get_trades():
    """获取历史交易记录（支持分页+策略过滤）"""
    strategy_id = request.args.get('strategy_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    page_size = min(page_size, 100)
    offset = (page - 1) * page_size
    trades = db.get_trades(limit=page_size, offset=offset, strategy_id=strategy_id)
    total = db.get_trades_count(strategy_id=strategy_id)
    return jsonify({
        'trades': trades,
        'page': page,
        'page_size': page_size,
        'total': total,
        'total_pages': (total + page_size - 1) // page_size,
        'has_more': page * page_size < total
    })


@trading_bp.route('/api/stats')
def get_stats():
    """获取交易统计（支持按策略过滤）"""
    strategy_id = request.args.get('strategy_id', type=int)
    return jsonify(db.get_trade_stats(strategy_id=strategy_id))


@trading_bp.route('/api/equity')
def get_equity():
    """获取净值曲线（支持按策略过滤）"""
    strategy_id = request.args.get('strategy_id', type=int)
    curve = db.get_equity_curve(days=60, strategy_id=strategy_id)
    return jsonify(curve)


@trading_bp.route('/api/risk/check', methods=['POST'])
def risk_check():
    """风控检查：下单前验证"""
    data = request.json
    action = data.get('action')
    stock_code = data.get('stock_code')
    shares = int(data.get('shares', 0))
    price = float(data.get('price', 0))

    errors = []
    account = db.get_account()

    if action == 'buy':
        cost = price * shares * 1.0003
        if cost > 10000:
            errors.append(f'单票金额 ¥{cost:.0f} 超过 ¥10,000 上限')
        positions = db.get_positions()
        pos_value = sum(p['avg_cost'] * p['shares'] for p in positions)
        new_total = pos_value + cost
        if account['total_value'] > 0 and new_total / account['total_value'] > 0.20:
            errors.append(f'仓位将达 {(new_total/account["total_value"]*100):.1f}%，超过 20% 上限')
        if cost > account['cash']:
            errors.append(f'资金不足，需要 ¥{cost:.0f}，可用 ¥{account["cash"]:.0f}')
    elif action == 'sell':
        position = db.get_position(stock_code)
        if not position:
            errors.append('没有该股票持仓')
        elif position['shares'] < shares:
            errors.append(f'持仓不足，持有 {position["shares"]} 股')

    return jsonify({'pass': len(errors) == 0, 'errors': errors})


@trading_bp.route('/api/trade', methods=['POST'])
def execute_trade():
    """执行交易 (带风控+T+1+交易时间检查)"""
    data = request.json
    action = data.get('action')
    stock_code = data.get('stock_code')
    shares = int(data.get('shares', 100))

    # === 检查1：交易时间 ===
    if not is_market_open():
        return jsonify({"error": "非交易时间 (A股09:30-11:30/13:00-15:00)"}), 400

    account = db.get_account()

    # 获取当前价（腾讯API）
    try:
        quotes = get_tencent_quote([stock_code])
        if stock_code not in quotes or quotes[stock_code]['price'] == 0:
            return jsonify({"error": "股票不存在或停牌"}), 400
        price = quotes[stock_code]['price']
        name = quotes[stock_code]['name']
    except Exception as e:
        logger.error(f"获取行情失败: {e}")
        return jsonify({"error": f"获取行情失败: {str(e)}"}), 500

    # 策略ID支持
    strategy_id = int(data.get('strategy_id', 1))
    strategy = db.get_strategy(strategy_id)
    if not strategy:
        return jsonify({'error': '策略不存在'}), 404

    commission = 0
    profit = 0
    new_cash = account['cash']

    if action == 'buy':
        amount = price * shares
        commission = calc_buy_commission(amount)
        cost = amount + commission

        if cost > account['cash']:
            return jsonify({"error": "资金不足"}), 400

        # === 策略资金隔离检查 ===
        strategy_positions = db.get_positions(strategy_id=strategy_id)
        strategy_used = sum(p['avg_cost'] * p['shares'] for p in strategy_positions)
        strategy_capital = strategy.get('capital', 100000)
        if strategy_used + cost > strategy_capital:
            return jsonify({
                "error": f"策略[{strategy['name']}]资金超限：已用¥{strategy_used:.0f} + 本次¥{cost:.0f} = ¥{strategy_used+cost:.0f}，上限¥{strategy_capital:.0f}"
            }), 400

        new_cash = account['cash'] - cost
        bj_tz = timezone(timedelta(hours=8))
        now_bj = datetime.now(bj_tz).strftime('%Y-%m-%d %H:%M:%S')
        position = db.get_position(stock_code)

        if position:
            total_shares = position['shares'] + shares
            total_cost = position['avg_cost'] * position['shares'] + amount
            new_avg_cost = total_cost / total_shares
            db.upsert_position(stock_code, name, total_shares, new_avg_cost, strategy_id=strategy_id)
        else:
            db.upsert_position(stock_code, name, shares, price, buy_date=now_bj, strategy_id=strategy_id)

    elif action == 'sell':
        position = db.get_position(stock_code)
        if not position:
            return jsonify({"error": "没有持仓"}), 400
        if position['shares'] < shares:
            return jsonify({"error": "持仓不足"}), 400

        # === 检查2：T+1 ===
        bj_tz = timezone(timedelta(hours=8))
        today = datetime.now(bj_tz).strftime('%Y-%m-%d')
        buy_date_raw = position.get('buy_date') or ''
        buy_date = buy_date_raw.split(' ')[0] if buy_date_raw else ''
        if buy_date == today:
            return jsonify({"error": f"T+1规则：{stock_code}今日买入不可卖出"}), 400

        amount = price * shares
        commission = calc_sell_commission(amount)
        revenue = amount - commission
        profit = (price - position['avg_cost']) * shares - commission
        new_cash = account['cash'] + revenue

        remaining = position['shares'] - shares
        if remaining == 0:
            db.delete_position(stock_code)
        else:
            db.upsert_position(stock_code, name, remaining, position['avg_cost'])

    # 更新账户
    positions = db.get_positions()
    total_value = new_cash
    try:
        codes = [p['stock_code'] for p in positions]
        quotes = get_tencent_quote(codes) if codes else {}
        for pos in positions:
            code = pos['stock_code']
            if code in quotes and quotes[code]['price'] > 0:
                total_value += quotes[code]['price'] * pos['shares']
            else:
                total_value += pos['avg_cost'] * pos['shares']
    except Exception as e:
        logger.warning(f"更新总资产时获取行情失败: {e}")
        for pos in positions:
            total_value += pos['avg_cost'] * pos['shares']

    db.update_account(new_cash, total_value)

    # 记录交易
    trade_id = db.add_trade(
        action, stock_code, name, price, shares,
        price * shares, commission, profit, data.get('reason', ''),
        strategy_id=strategy_id
    )

    # 记录净值
    position_value = total_value - new_cash
    db.add_equity_record(date.today().isoformat(), total_value, new_cash, position_value, strategy_id=0)
    db.add_equity_record(date.today().isoformat(), total_value, new_cash, position_value, strategy_id=strategy_id)

    return jsonify({
        "success": True,
        "trade_id": trade_id,
        "trade": {
            "id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "stock_code": stock_code,
            "stock_name": name,
            "price": price,
            "shares": shares,
            "amount": price * shares,
            "commission": round(commission, 2),
            "profit": round(profit, 2)
        },
        "portfolio": {
            "cash": round(new_cash, 2),
            "total_value": round(total_value, 2),
            "total_profit": round(total_value - account.get('initial_capital', 300000.0), 2)
        }
    })
