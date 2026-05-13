"""
策略管理路由: /api/strategies/*
"""
import logging
from flask import Blueprint, jsonify, request

import database as db

logger = logging.getLogger(__name__)

strategy_bp = Blueprint('strategy', __name__)


@strategy_bp.route('/api/strategies')
def get_strategies():
    """获取策略列表"""
    strategies = db.get_strategies()
    result = []
    for s in strategies:
        stats = db.get_trade_stats(strategy_id=s['id'])
        positions = db.get_positions(strategy_id=s['id'])
        s['stats'] = stats
        s['position_count'] = len(positions)
        result.append(s)
    return jsonify(result)


@strategy_bp.route('/api/strategies/<int:strategy_id>')
def get_strategy_detail(strategy_id):
    """获取策略详情"""
    strategy = db.get_strategy(strategy_id)
    if not strategy:
        return jsonify({'error': '策略不存在'}), 404

    stats = db.get_trade_stats(strategy_id=strategy_id)
    positions = db.get_positions(strategy_id=strategy_id)
    equity = db.get_equity_curve(days=60, strategy_id=strategy_id)

    return jsonify({
        **strategy,
        'stats': stats,
        'positions': positions,
        'equity_curve': equity,
    })


@strategy_bp.route('/api/strategies/<int:strategy_id>/toggle', methods=['POST'])
def toggle_strategy(strategy_id):
    """启用/禁用策略"""
    data = request.get_json() or {}
    is_active = data.get('is_active', True)
    db.update_strategy_activity(strategy_id, is_active)
    return jsonify({'success': True, 'is_active': is_active})


@strategy_bp.route('/api/strategies/<int:strategy_id>/capital', methods=['POST'])
def update_strategy_capital(strategy_id):
    """更新策略资金分配"""
    data = request.get_json() or {}
    capital = float(data.get('capital', 0))
    if capital < 0:
        return jsonify({'error': '资金不能为负数'}), 400
    db.update_strategy_capital(strategy_id, capital)
    return jsonify({'success': True, 'capital': capital})


@strategy_bp.route('/api/strategies/sync-capital')
def sync_strategy_capital():
    """同步策略资金分配（自动计算）"""
    account = db.get_account()
    strategies = db.get_strategies(active_only=True)
    total_capital = account.get('total_value', 0)
    active_count = len(strategies)

    each = 0
    if active_count > 0:
        each = round(total_capital / active_count, 2)
        for s in strategies:
            db.update_strategy_capital(s['id'], each)

    return jsonify({'success': True, 'total': total_capital, 'per_strategy': each})
