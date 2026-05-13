"""
策略快照服务 (Strategy Snapshot)

借鉴 QuantDinger 的 StrategySnapshotResolver，为每次交易保存策略参数快照。

用途：
- 每次交易时记录当时的策略参数版本
- 复盘时可以追溯"当时用的什么参数做的决策"
- 参数调整后，可以对比新旧参数的表现差异
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

import database as db

logger = logging.getLogger(__name__)


class StrategySnapshot:
    """策略参数快照管理"""

    def __init__(self):
        self._ensure_table()

    def _ensure_table(self):
        """确保快照表存在"""
        with db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id INTEGER NOT NULL,
                    version TEXT NOT NULL,
                    params TEXT NOT NULL,
                    description TEXT,
                    performance_summary TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshot_strategy_active
                ON strategy_snapshots(strategy_id, is_active, created_at DESC)
            """)

    def save_snapshot(
        self,
        strategy_id: int,
        params: Dict[str, Any],
        description: str = "",
        version: Optional[str] = None,
    ) -> int:
        """
        保存策略参数快照

        Returns: snapshot_id
        """
        if not version:
            # 自动生成版本号: v{策略id}.{序号}
            with db.get_connection() as conn:
                row = conn.execute("""
                    SELECT COUNT(*) as cnt FROM strategy_snapshots
                    WHERE strategy_id = ?
                """, (strategy_id,)).fetchone()
                count = row["cnt"] if row else 0
                version = f"v{strategy_id}.{count + 1}"

        with db.get_connection() as conn:
            # 将之前的快照标记为非活跃
            conn.execute("""
                UPDATE strategy_snapshots SET is_active = 0
                WHERE strategy_id = ? AND is_active = 1
            """, (strategy_id,))

            # 插入新快照
            cursor = conn.execute("""
                INSERT INTO strategy_snapshots
                (strategy_id, version, params, description, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (
                strategy_id,
                version,
                json.dumps(params, ensure_ascii=False),
                description,
            ))
            return cursor.lastrowid

    def get_active_snapshot(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """获取当前活跃的策略快照"""
        with db.get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM strategy_snapshots
                WHERE strategy_id = ? AND is_active = 1
                ORDER BY created_at DESC
                LIMIT 1
            """, (strategy_id,)).fetchone()

        if not row:
            return None
        result = dict(row)
        result["params"] = json.loads(result["params"]) if result["params"] else {}
        return result

    def get_snapshot_history(self, strategy_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取策略快照历史"""
        with db.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM strategy_snapshots
                WHERE strategy_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (strategy_id, limit)).fetchall()

        results = []
        for row in rows:
            r = dict(row)
            r["params"] = json.loads(r["params"]) if r["params"] else {}
            results.append(r)
        return results

    def compare_snapshots(self, snapshot_id_a: int, snapshot_id_b: int) -> Dict[str, Any]:
        """对比两个快照的参数差异"""
        with db.get_connection() as conn:
            a = conn.execute("SELECT * FROM strategy_snapshots WHERE id = ?", (snapshot_id_a,)).fetchone()
            b = conn.execute("SELECT * FROM strategy_snapshots WHERE id = ?", (snapshot_id_b,)).fetchone()

        if not a or not b:
            return {"error": "快照不存在"}

        params_a = json.loads(a["params"]) if a["params"] else {}
        params_b = json.loads(b["params"]) if b["params"] else {}

        # 找出差异
        all_keys = set(list(params_a.keys()) + list(params_b.keys()))
        changes = {}
        for key in sorted(all_keys):
            val_a = params_a.get(key)
            val_b = params_b.get(key)
            if val_a != val_b:
                changes[key] = {"before": val_a, "after": val_b}

        return {
            "snapshot_a": {"id": a["id"], "version": a["version"], "created_at": a["created_at"]},
            "snapshot_b": {"id": b["id"], "version": b["version"], "created_at": b["created_at"]},
            "changes": changes,
            "total_params": len(all_keys),
            "changed_params": len(changes),
        }

    def update_performance(self, snapshot_id: int, performance: Dict[str, Any]):
        """更新快照的表现数据（用于校准后回填）"""
        with db.get_connection() as conn:
            conn.execute("""
                UPDATE strategy_snapshots
                SET performance_summary = ?
                WHERE id = ?
            """, (json.dumps(performance, ensure_ascii=False), snapshot_id))


# 预定义的策略参数模板
STRATEGY_PARAMS = {
    1: {  # 一夜持股法 v2.3
        "name": "一夜持股法",
        "version": "v2.3",
        "buy_conditions": {
            "change_pct_min": 3.0,
            "change_pct_max": 5.0,
            "turnover_min": 3.0,
            "turnover_max": 10.0,
            "rsi_max": 65,
            "volume_ratio_min": 1.5,
            "market_cap_min_yi": 50,
            "market_cap_max_yi": 200,
        },
        "sell_conditions": {
            "take_profit_pct": 5.0,
            "take_profit_max_pct": 8.0,
            "trailing_stop_pct": -2.0,
            "stop_loss_pct": -2.0,
            "low_open_wait_minutes": 15,
        },
        "timing": {
            "buy_window_start": "14:50",
            "buy_window_end": "14:55",
            "sell_window_start": "09:30",
            "sell_window_end": "10:30",
        },
    },
    2: {  # 价值投资
        "name": "价值投资",
        "version": "v1.0",
        "buy_conditions": {
            "pe_max": 15,
            "roe_min": 15,
            "debt_ratio_max": 50,
            "safety_margin_pct": 20,
        },
        "sell_conditions": {
            "take_profit_pct": 30,
            "stop_loss_pct": -10,
            "hold_months_max": 3,
        },
    },
    3: {  # 趋势跟踪
        "name": "趋势跟踪",
        "version": "v1.0",
        "buy_conditions": {
            "ma20_above_ma60": True,
            "volume_ratio_min": 1.5,
            "recent_5d_change_min": 3.0,
            "recent_5d_change_max": 10.0,
            "rsi_max": 70,
        },
        "sell_conditions": {
            "take_profit_pct": 10,
            "trailing_stop_pct": -3,
            "stop_loss_pct": -5,
        },
    },
}


def init_strategy_snapshots():
    """初始化：为每个策略创建初始快照"""
    snapshot_svc = StrategySnapshot()
    for strategy_id, params in STRATEGY_PARAMS.items():
        existing = snapshot_svc.get_active_snapshot(strategy_id)
        if not existing:
            snapshot_svc.save_snapshot(
                strategy_id=strategy_id,
                params=params,
                description=f"初始参数 {params.get('version', 'v1.0')}",
            )
            logger.info(f"[Snapshot] 策略{strategy_id} 初始快照已创建")
