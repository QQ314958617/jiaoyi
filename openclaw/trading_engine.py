"""
蛋蛋自动化交易引擎
==================
基于 Claude Code 四大核心系统（Task/Hooks/Store/Coordinator）

架构：
┌─────────────────────────────────────────────────────────┐
│                    AI工作室状态看板                       │
│         (researching → executing → idle)                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│               TradingEngine (Coordinator)                │
│  • 多标并行分析（Coordinator）                            │
│  • 交易决策制定                                          │
│  • 结果综合汇报                                          │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ TaskManager   │  │ HooksManager  │  │ TradingStore  │
│ 看盘任务      │  │ 定时触发      │  │ 状态管理      │
│ 后台监控     │  │ 大盘信号     │  │ 持仓/现金    │
└───────────────┘  └───────────────┘  └───────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌───────────────┐
                    │  Flask API    │
                    │ /api/trade    │
                    │ /api/portfolio│
                    └───────────────┘
"""
import json
import time
import threading
import requests
from dataclasses import dataclass, field
from datetime import datetime, time as dtime
from typing import Dict, List, Optional, Callable
from enum import Enum

# ============================================================================
# 导入四大核心系统
# ============================================================================

import sys
sys.path.insert(0, '/root/.openclaw/workspace')

from openclaw.task_base import TaskType, TaskStatus
from openclaw.task_manager import task_manager
from openclaw.hooks_base import HookEvent, HookInput, HookConfig, HookType
from openclaw.hooks_manager import hooks_manager
from openclaw.store import create_store
from openclaw.coordinator import Coordinator, AgentTool, SendMessageTool, WorkerStatus


# ============================================================================
# 交易引擎状态
# ============================================================================

class TradingPhase(str, Enum):
    """交易阶段"""
    IDLE = "idle"           # 空闲
    RESEARCH = "researching" # 研究分析
    DECISION = "writing"     # 决策制定
    EXECUTING = "executing"  # 执行交易
    SYNCING = "syncing"      # 同步记录
    MONITORING = "monitoring" # 监控中


@dataclass
class Position:
    """持仓"""
    code: str
    name: str
    shares: int
    cost: float
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.shares * self.current_price

    @property
    def profit_loss(self) -> float:
        return self.market_value - (self.shares * self.cost)

    @property
    def profit_loss_pct(self) -> float:
        cost_total = self.shares * self.cost
        if cost_total == 0:
            return 0
        return (self.profit_loss / cost_total) * 100


@dataclass
class AccountState:
    """账户状态"""
    cash: float = 50000.0
    positions: Dict[str, Position] = field(default_factory=dict)
    total_value: float = 50000.0

    def update_value(self):
        """更新总市值"""
        pos_value = sum(p.market_value for p in self.positions.values())
        self.total_value = self.cash + pos_value


@dataclass
class MarketState:
    """大盘状态"""
    index_code: str = "000001"
    index_name: str = "上证指数"
    price: float = 0.0
    ma5: float = 0.0
    ma10: float = 0.0
    volume: float = 0.0
    timestamp: str = ""

    @property
    def is_stable_above_ma5(self) -> bool:
        """指数站稳5日线"""
        return self.price > self.ma5 > 0

    @property
    def is_ma5_above_ma10(self) -> bool:
        """MA5 > MA10（多头排列）"""
        return self.ma5 > self.ma10 > 0

    @property
    def can_build_position(self) -> bool:
        """是否可以建仓"""
        return self.is_stable_above_ma5 and self.is_ma5_above_ma10


@dataclass
class EngineState:
    """引擎全局状态"""
    phase: TradingPhase = TradingPhase.IDLE
    description: str = ""
    last_update: str = ""
    account: AccountState = field(default_factory=AccountState)
    market: MarketState = field(default_factory=MarketState)
    debug_mode: bool = True


# ============================================================================
# 全局状态存储
# ============================================================================

engine_store = create_store(EngineState())


def get_state() -> EngineState:
    return engine_store.get_state()


def update_phase(phase: TradingPhase, description: str = ""):
    """更新引擎阶段"""
    def updater(state: EngineState):
        return EngineState(
            phase=phase,
            description=description,
            last_update=datetime.now().strftime("%H:%M:%S"),
            account=state.account,
            market=state.market,
            debug_mode=state.debug_mode,
        )
    engine_store.set_state(updater)


def update_market(price: float, ma5: float, ma10: float, volume: float):
    """更新大盘状态"""
    def updater(state: EngineState):
        return EngineState(
            phase=state.phase,
            description=state.description,
            last_update=datetime.now().strftime("%H:%M:%S"),
            account=state.account,
            market=MarketState(
                price=price,
                ma5=ma5,
                ma10=ma10,
                volume=volume,
                timestamp=datetime.now().strftime("%H:%M:%S"),
            ),
            debug_mode=state.debug_mode,
        )
    engine_store.set_state(updater)


def update_account(cash: float, positions: Dict[str, Position]):
    """更新账户状态"""
    def updater(state: EngineState):
        account = AccountState(cash=cash, positions=positions)
        account.update_value()
        return EngineState(
            phase=state.phase,
            description=state.description,
            last_update=datetime.now().strftime("%H:%M:%S"),
            account=account,
            market=state.market,
            debug_mode=state.debug_mode,
        )
    engine_store.set_state(updater)


# ============================================================================
# API客户端
# ============================================================================

API_BASE = "http://localhost/api"


def api_get(endpoint: str) -> Optional[dict]:
    """GET请求API"""
    try:
        r = requests.get(f"{API_BASE}/{endpoint}", timeout=5)
        return r.json()
    except Exception as e:
        print(f"[API GET Error] {endpoint}: {e}")
        return None


def api_post(endpoint: str, data: dict) -> Optional[dict]:
    """POST请求API"""
    try:
        r = requests.post(f"{API_BASE}/{endpoint}", json=data, timeout=10)
        return r.json()
    except Exception as e:
        print(f"[API POST Error] {endpoint}: {e}")
        return None


# ============================================================================
# 市场数据获取
# ============================================================================

def fetch_market_data() -> Optional[MarketState]:
    """获取大盘数据"""
    data = api_get("index")
    if not data:
        return None

    return MarketState(
        index_code=data.get("code", "000001"),
        index_name=data.get("name", "上证指数"),
        price=data.get("price", 0),
        ma5=data.get("ma5", 0),
        ma10=data.get("ma10", 0),
        volume=data.get("volume", 0),
        timestamp=datetime.now().strftime("%H:%M:%S"),
    )


def fetch_account_data() -> Optional[AccountState]:
    """获取账户数据"""
    data = api_get("portfolio")
    if not data:
        return None

    positions = {}
    for code, pos in data.get("positions", {}).items():
        positions[code] = Position(
            code=code,
            name=pos.get("name", code),
            shares=pos.get("shares", 0),
            cost=pos.get("cost", 0),
            current_price=pos.get("current_price", 0),
        )

    return AccountState(
        cash=data.get("cash", 0),
        positions=positions,
        total_value=data.get("total_value", 0),
    )


def fetch_position_quotes() -> Dict[str, dict]:
    """获取持仓股行情"""
    data = api_get("quotes/batch")
    if not data:
        return {}
    return {item["code"]: item for item in data}


# ============================================================================
# 交易策略检查
# ============================================================================

def check_stop_loss(position: Position) -> Optional[str]:
    """检查止损"""
    loss_pct = -position.profit_loss_pct
    if loss_pct >= 8:
        return f"触发止损！亏损 {-position.profit_loss_pct:.2f}%"
    return None


def check_take_profit(position: Position) -> Optional[str]:
    """检查止盈"""
    profit_pct = position.profit_loss_pct
    if profit_pct >= 20:
        return f"清仓！盈利 {profit_pct:.2f}%"
    elif profit_pct >= 15:
        return f"卖1/3！盈利 {profit_pct:.2f}%"
    elif profit_pct >= 10:
        return f"卖1/3！盈利 {profit_pct:.2f}%"
    return None


def check_buy_signal(stock_quote: dict, market: MarketState) -> Optional[str]:
    """检查买入信号"""
    if not market.can_build_position:
        return None

    # 简化：基于价格变化和成交量
    change_pct = abs(stock_quote.get("change_pct", 0))
    volume = stock_quote.get("volume", 0)

    # 放量上涨 + 大盘多头 = 买入信号
    if change_pct > 1.0 and volume > 100000:
        return f"放量上涨 {change_pct:.2f}%，买入信号"

    return None


# ============================================================================
# Coordinator: 并行分析器
# ============================================================================

class ParallelAnalyzer:
    """
    并行分析器
    使用 Coordinator 模式并行分析多个标的
    """

    def __init__(self):
        self.coord = Coordinator("并行分析器")
        self.agent = AgentTool(self.coord)

    def analyze_stocks(self, stock_codes: List[str]) -> Dict[str, str]:
        """并行分析多个股票"""
        update_phase(TradingPhase.RESEARCH, f"并行分析 {len(stock_codes)} 个标的")

        for code in stock_codes:
            self.agent(
                description=f"分析{code}",
                prompt=self._build_analysis_prompt(code),
            )

        # 等待完成
        max_wait = 30
        start = time.time()
        while len(self.coord.completed_workers()) < len(stock_codes):
            if time.time() - start > max_wait:
                break
            time.sleep(0.5)

        # 收集结果
        results = {}
        for worker in self.coord.completed_workers():
            results[worker.description] = worker.result or "无结果"

        return results

    def _build_analysis_prompt(self, code: str) -> str:
        """构建分析提示"""
        return f"""分析股票 {code} 的交易机会：

1. 获取实时行情（调用 /api/quote/{code}）
2. 检查技术指标：
   - RSI是否低于35（超卖）
   - 是否放量突破
   - 距离止损位（成本-8%）
   - 距离止盈位（成本+10%/+15%/+20%）

3. 给出操作建议：强烈买入/买入/持有/观望/卖出

请简洁回复，格式：
股票: {code}
当前价格: xxx
RSI: xxx
操作建议: xxx"""


# ============================================================================
# 决策引擎
# ============================================================================

class DecisionEngine:
    """
    决策引擎
    基于分析结果制定交易决策
    """

    def __init__(self):
        self.coord = Coordinator("决策引擎")
        self.send = SendMessageTool(self.coord)

    def make_decisions(
        self,
        analysis_results: Dict[str, str],
        account: AccountState,
        market: MarketState,
    ) -> List[dict]:
        """制定交易决策"""
        update_phase(TradingPhase.DECISION, "综合分析制定决策...")

        decisions = []

        # 1. 检查持仓是否需要止损/止盈
        for code, position in account.positions.items():
            stop_loss_msg = check_stop_loss(position)
            if stop_loss_msg:
                decisions.append({
                    "action": "SELL",
                    "code": code,
                    "shares": position.shares,
                    "reason": stop_loss_msg,
                    "priority": 1,  # 高优先级
                })
                continue

            take_profit_msg = check_take_profit(position)
            if take_profit_msg:
                # 分批止盈
                shares_to_sell = position.shares // 3
                decisions.append({
                    "action": "SELL",
                    "code": code,
                    "shares": shares_to_sell,
                    "reason": take_profit_msg,
                    "priority": 2,
                })

        # 2. 检查是否可以建仓
        if market.can_build_position and account.cash >= 10000:
            # 找最佳买入信号
            for name, result in analysis_results.items():
                if "买入" in result:
                    code = name.replace("分析", "")
                    if code not in account.positions:
                        decisions.append({
                            "action": "BUY",
                            "code": code,
                            "shares": 100,  # 固定买100股
                            "reason": result[:100],
                            "priority": 3,
                        })
                        break  # 只买一个

        # 按优先级排序
        decisions.sort(key=lambda x: x["priority"])
        return decisions


# ============================================================================
# 执行引擎
# ============================================================================

class ExecutionEngine:
    """
    执行引擎
    执行交易决策
    """

    def __init__(self):
        self.coord = Coordinator("执行引擎")
        self.send = SendMessageTool(self.coord)

    def execute_decisions(self, decisions: List[dict]) -> List[dict]:
        """执行交易决策"""
        results = []

        for decision in decisions:
            update_phase(TradingPhase.EXECUTING, f"{decision['action']} {decision['code']}...")

            result = api_post("trade", {
                "action": decision["action"].lower(),
                "stock_code": decision["code"],
                "shares": decision["shares"],
                "reason": decision.get("reason", ""),
            })

            if result:
                results.append({
                    "success": result.get("success", False),
                    "decision": decision,
                    "result": result,
                })

            time.sleep(0.5)  # 避免过快

        return results


# ============================================================================
# 主交易引擎
# ============================================================================

class TradingEngine:
    """
    蛋蛋自动化交易引擎
    整合四大核心系统
    """

    def __init__(self):
        self.analyzer = ParallelAnalyzer()
        self.decision_engine = DecisionEngine()
        self.executor = ExecutionEngine()
        self._running = False
        self._monitor_task_id: Optional[str] = None

        # 注册钩子
        self._register_hooks()

    def _register_hooks(self):
        """注册定时钩子"""

        def market_check_hook(input: HookInput) -> dict:
            """大盘状态检查钩子"""
            market = fetch_market_data()
            if market:
                update_market(market.price, market.ma5, market.ma10, market.volume)
                return {
                    "continue": True,
                    "additional_context": f"大盘{market.price}，MA5={market.ma5}，MA10={market.ma10}，可建仓={market.can_build_position}",
                }
            return {"continue": True}

        # 注册SessionStart钩子
        hooks_manager.add_function_hook(
            event=HookEvent.SESSION_START,
            matcher="*",
            callback=market_check_hook,
            error_message="大盘检查失败",
        )

        print("[TradingEngine] 钩子注册完成")

    def run_full_cycle(self) -> dict:
        """
        执行完整交易周期
        返回执行结果
        """
        print("\n" + "=" * 60)
        print("🥚 蛋蛋交易引擎 - 完整周期")
        print("=" * 60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "steps": [],
        }

        # 步骤1: 获取数据
        update_phase(TradingPhase.RESEARCH, "获取市场数据...")
        print("\n📊 [1/5] 获取市场数据...")

        market = fetch_market_data()
        if market:
            update_market(market.price, market.ma5, market.ma10, market.volume)
            print(f"   大盘: {market.price} | MA5={market.ma5} | MA10={market.ma10}")
            print(f"   可建仓: {market.can_build_position}")
            results["steps"].append({
                "step": "market_data",
                "success": True,
                "data": {
                    "price": market.price,
                    "ma5": market.ma5,
                    "ma10": market.ma10,
                }
            })
        else:
            print("   ❌ 获取市场数据失败")
            results["steps"].append({"step": "market_data", "success": False})
            update_phase(TradingPhase.IDLE, "获取数据失败")
            return results

        # 步骤2: 获取账户
        update_phase(TradingPhase.RESEARCH, "获取账户数据...")
        print("\n💰 [2/5] 获取账户数据...")

        account = fetch_account_data()
        if account:
            update_account(account.cash, account.positions)
            print(f"   现金: ¥{account.cash:.2f}")
            print(f"   持仓: {len(account.positions)} 只")
            print(f"   总市值: ¥{account.total_value:.2f}")
            results["steps"].append({
                "step": "account_data",
                "success": True,
                "data": {
                    "cash": account.cash,
                    "positions": len(account.positions),
                    "total_value": account.total_value,
                }
            })
        else:
            print("   ❌ 获取账户数据失败")
            results["steps"].append({"step": "account_data", "success": False})
            update_phase(TradingPhase.IDLE, "获取账户失败")
            return results

        # 步骤3: 并行分析持仓股
        update_phase(TradingPhase.RESEARCH, "分析持仓股...")
        print("\n🔍 [3/5] 分析持仓股...")

        position_codes = list(account.positions.keys())
        if position_codes:
            analysis = self.analyzer.analyze_stocks(position_codes)
            print(f"   分析了 {len(analysis)} 只持仓股")
        else:
            analysis = {}
            print("   无持仓，跳过")

        results["steps"].append({
            "step": "analysis",
            "success": True,
            "data": {"analyzed": len(analysis)},
        })

        # 步骤4: 制定决策
        update_phase(TradingPhase.DECISION, "制定交易决策...")
        print("\n📋 [4/5] 制定交易决策...")

        decisions = self.decision_engine.make_decisions(analysis, account, market)
        if decisions:
            print(f"   生成 {len(decisions)} 个交易决策")
            for d in decisions[:3]:  # 只显示前3个
                print(f"   - {d['action']} {d['code']} x {d['shares']}: {d['reason'][:50]}...")
        else:
            print("   无需交易操作")

        results["steps"].append({
            "step": "decisions",
            "success": True,
            "data": {"decisions": len(decisions), "items": decisions},
        })

        # 步骤5: 执行决策
        update_phase(TradingPhase.EXECUTING, "执行交易...")
        print("\n⚡ [5/5] 执行交易...")

        if decisions:
            exec_results = self.executor.execute_decisions(decisions)
            success_count = sum(1 for r in exec_results if r.get("success"))
            print(f"   执行完成: {success_count}/{len(decisions)} 成功")
            results["steps"].append({
                "step": "execution",
                "success": True,
                "data": {"executed": len(exec_results), "success": success_count},
            })
        else:
            print("   无需执行")
            results["steps"].append({"step": "execution", "success": True, "data": {}})

        # 完成
        update_phase(TradingPhase.IDLE, "待命中")
        print("\n✅ 交易周期完成")
        print("=" * 60)

        return results

    def start_monitoring(self, interval_seconds: int = 300):
        """启动后台监控"""
        def monitor_loop():
            self._running = True
            while self._running:
                try:
                    self.run_full_cycle()
                    time.sleep(interval_seconds)
                except Exception as e:
                    print(f"[Monitor Error] {e}")
                    time.sleep(60)  # 出错后等1分钟再试

        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        print(f"[TradingEngine] 后台监控已启动，间隔 {interval_seconds} 秒")

    def stop_monitoring(self):
        """停止后台监控"""
        self._running = False
        print("[TradingEngine] 后台监控已停止")


# ============================================================================
# 便捷函数
# ============================================================================

# 全局引擎实例
_engine: Optional[TradingEngine] = None


def get_engine() -> TradingEngine:
    """获取全局引擎实例"""
    global _engine
    if _engine is None:
        _engine = TradingEngine()
    return _engine


def run_trading_cycle() -> dict:
    """运行一次完整交易周期"""
    return get_engine().run_full_cycle()


def start_auto_trading(interval_seconds: int = 300):
    """启动自动交易（后台）"""
    get_engine().start_monitoring(interval_seconds)


def get_engine_status() -> dict:
    """获取引擎状态"""
    state = get_state()
    return {
        "phase": state.phase.value,
        "description": state.description,
        "last_update": state.last_update,
        "market": {
            "price": state.market.price,
            "ma5": state.market.ma5,
            "ma10": state.market.ma10,
            "can_build": state.market.can_build_position,
        },
        "account": {
            "cash": state.account.cash,
            "positions": len(state.account.positions),
            "total_value": state.account.total_value,
        },
    }


# ============================================================================
# Flask 集成
# ============================================================================

def integrate_with_flask(app):
    """集成到Flask应用"""

    @app.route("/api/engine/status", methods=["GET"])
    def engine_status():
        """获取引擎状态"""
        return jsonify(get_engine_status())

    @app.route("/api/engine/run", methods=["POST"])
    def engine_run():
        """触发一次交易周期"""
        result = run_trading_cycle()
        return jsonify({"success": True, "result": result})

    @app.route("/api/engine/start", methods=["POST"])
    def engine_start():
        """启动自动交易"""
        data = request.get_json() or {}
        interval = data.get("interval", 300)
        start_auto_trading(interval)
        return jsonify({"success": True, "message": f"自动交易已启动，间隔 {interval} 秒"})

    @app.route("/api/engine/stop", methods=["POST"])
    def engine_stop():
        """停止自动交易"""
        get_engine().stop_monitoring()
        return jsonify({"success": True, "message": "自动交易已停止"})

    print("[TradingEngine] Flask集成完成")


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    print("🥚 蛋蛋自动化交易引擎")
    print("=" * 40)

    # 创建并运行引擎
    engine = get_engine()
    result = engine.run_full_cycle()

    print("\n📊 执行结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n📈 当前状态:")
    print(json.dumps(get_engine_status(), indent=2, ensure_ascii=False))
