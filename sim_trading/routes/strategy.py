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


# ============================================================
# 策略校准 & 快照 & 反思 API
# ============================================================

@strategy_bp.route('/api/strategies/<int:strategy_id>/calibrate', methods=['POST'])
def calibrate_strategy(strategy_id):
    """运行策略参数校准"""
    from services.calibration import StrategyCalibrator
    data = request.get_json() or {}
    lookback_days = int(data.get('lookback_days', 30))

    calibrator = StrategyCalibrator()
    if strategy_id == 1:
        result = calibrator.calibrate_overnight(lookback_days=lookback_days)
    else:
        return jsonify({'error': '该策略暂不支持自动校准'}), 400

    if not result:
        return jsonify({'message': '样本不足，无法校准', 'min_samples': 5})

    from dataclasses import asdict
    return jsonify(asdict(result))


@strategy_bp.route('/api/strategies/<int:strategy_id>/calibration')
def get_calibration_history(strategy_id):
    """获取策略校准历史"""
    from services.calibration import StrategyCalibrator
    calibrator = StrategyCalibrator()
    history = calibrator.get_calibration_history(strategy_id, limit=10)
    latest = calibrator.get_latest_calibration(strategy_id)
    return jsonify({'latest': latest, 'history': history})


@strategy_bp.route('/api/strategies/<int:strategy_id>/snapshots')
def get_strategy_snapshots(strategy_id):
    """获取策略参数快照历史"""
    from services.snapshot import StrategySnapshot
    svc = StrategySnapshot()
    active = svc.get_active_snapshot(strategy_id)
    history = svc.get_snapshot_history(strategy_id, limit=10)
    return jsonify({'active': active, 'history': history})


@strategy_bp.route('/api/strategies/<int:strategy_id>/snapshots', methods=['POST'])
def create_strategy_snapshot(strategy_id):
    """手动创建策略参数快照"""
    from services.snapshot import StrategySnapshot
    data = request.get_json() or {}
    params = data.get('params', {})
    description = data.get('description', '')

    if not params:
        return jsonify({'error': '参数不能为空'}), 400

    svc = StrategySnapshot()
    snapshot_id = svc.save_snapshot(
        strategy_id=strategy_id,
        params=params,
        description=description,
    )
    return jsonify({'success': True, 'snapshot_id': snapshot_id})


@strategy_bp.route('/api/strategies/snapshots/compare')
def compare_snapshots():
    """对比两个快照"""
    from services.snapshot import StrategySnapshot
    id_a = request.args.get('a', type=int)
    id_b = request.args.get('b', type=int)
    if not id_a or not id_b:
        return jsonify({'error': '需要参数 a 和 b (snapshot_id)'}), 400

    svc = StrategySnapshot()
    result = svc.compare_snapshots(id_a, id_b)
    return jsonify(result)


@strategy_bp.route('/api/reflection', methods=['POST'])
def run_reflection():
    """运行交易反思分析"""
    from services.reflection import ReflectionService
    data = request.get_json() or {}
    lookback_days = int(data.get('lookback_days', 7))

    svc = ReflectionService()
    results = svc.run_reflection(lookback_days=lookback_days)
    return jsonify(results)


@strategy_bp.route('/api/reflection/latest')
def get_latest_reflection():
    """获取最近一次反思结果"""
    import json
    with db.get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM daily_reviews
            WHERE tags LIKE '%自动反思%'
            ORDER BY timestamp DESC
            LIMIT 1
        """).fetchone()

    if not row:
        return jsonify({'message': '暂无反思记录'})
    return jsonify(dict(row))
