"""
蛋蛋交易系统集成模块
=====================
将四大核心系统（Task/Hooks/Store/Coordinator）应用于实际交易

集成架构：
1. Task System → 看盘任务管理（后台监控多个标的）
2. Hooks System → 定时触发（cron式监控）
3. Store → AI工作室状态 + 交易状态
4. Coordinator → 多标的同时分析
"""
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from task_base import TaskType, TaskStatus, generate_task_id
from task_manager import task_manager, TaskState
from hooks_base import HookEvent, HookInput, HookConfig, HookType
from hooks_manager import hooks_manager
from store import create_store
from coordinator import Coordinator, AgentTool, SendMessageTool, WorkerStatus


# ============================================================================
# 交易系统状态
# ============================================================================

class MarketStatus:
    """市场状态"""
    BULL = "BULL"        # 上涨趋势
    BEAR = "BEAR"        # 下跌趋势
    VOLATILE = "VOLATILE"  # 震荡


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
class TradingState:
    """交易状态"""
    cash: float = 50000.0
    positions: Dict[str, Position] = field(default_factory=dict)
    total_value: float = 50000.0

    def add_position(self, code: str, name: str, shares: int, cost: float):
        self.positions[code] = Position(code, name, shares, cost)

    def remove_position(self, code: str):
        self.positions.pop(code, None)


@dataclass
class MonitorState:
    """监控状态"""
    index_code: str = "000001"
    index_name: str = "上证指数"
    index_price: float = 0.0
    ma5: float = 0.0
    ma10: float = 0.0
    volume: float = 0.0
    status: str = MarketStatus.VOLATILE

    @property
    def is_stable_above_ma5(self) -> bool:
        return self.index_price > self.ma5 > 0

    @property
    def is_ma5_above_ma10(self) -> bool:
        return self.ma5 > self.ma10 > 0


@dataclass
class AIStudioState:
    """AI工作室状态"""
    status: str = "idle"  # researching | writing | executing | syncing | idle | error
    description: str = ""
    last_update: str = ""


@dataclass
class TradingAppState:
    """全局交易应用状态"""
    trading: TradingState = field(default_factory=TradingState)
    monitor: MonitorState = field(default_factory=MonitorState)
    ai_studio: AIStudioState = field(default_factory=AIStudioState)
    session_id: str = ""
    debug_mode: bool = False


# ============================================================================
# 交易系统 Store
# ============================================================================

# 全局状态存储
trading_store = create_store(TradingAppState())


def get_trading_state() -> TradingState:
    """获取交易状态"""
    return trading_store.get_state().trading


def get_monitor_state() -> MonitorState:
    """获取监控状态"""
    return trading_store.get_state().monitor


def update_trading_state(updater):
    """更新交易状态"""
    def update(state: TradingAppState):
        return TradingAppState(
            trading=updater(state.trading),
            monitor=state.monitor,
            ai_studio=state.ai_studio,
            session_id=state.session_id,
            debug_mode=state.debug_mode,
        )
    trading_store.set_state(update)


def update_monitor_state(**kwargs):
    """更新监控状态"""
    def update(state: TradingAppState):
        return TradingAppState(
            trading=state.trading,
            monitor=MonitorState(**{**state.monitor.__dict__, **kwargs}),
            ai_studio=state.ai_studio,
            session_id=state.session_id,
            debug_mode=state.debug_mode,
        )
    trading_store.set_state(update)


def update_ai_studio_status(status: str, description: str = ""):
    """更新AI工作室状态"""
    def update(state: TradingAppState):
        return TradingAppState(
            trading=state.trading,
            monitor=state.monitor,
            ai_studio=AIStudioState(
                status=status,
                description=description,
                last_update=datetime.now().strftime("%H:%M:%S"),
            ),
            session_id=state.session_id,
            debug_mode=state.debug_mode,
        )
    trading_store.set_state(update)


# ============================================================================
# Task System - 看盘任务
# ============================================================================

class MonitorTask:
    """
    看盘任务
    使用Task System管理后台监控任务
    """

    def __init__(self, name: str, stock_codes: List[str]):
        self.name = name
        self.stock_codes = stock_codes
        self.task_id: Optional[str] = None
        self._running = False
        self._abort_event = threading.Event()

    def start(self) -> str:
        """启动看盘任务"""
        self.task_id = task_manager.create_task(
            TaskType.LOCAL_BASH,
            self.name,
            tool_use_id=f"monitor-{'-'.join(self.stock_codes)}",
        ).id
        task_manager.start(self.task_id)
        self._running = True

        # 启动后台监控线程
        thread = threading.Thread(target=self._run_monitor, daemon=True)
        thread.start()

        return self.task_id

    def stop(self) -> bool:
        """停止看盘任务"""
        self._running = False
        self._abort_event.set()
        if self.task_id:
            return task_manager.kill(self.task_id)
        return False

    def _run_monitor(self):
        """执行监控（后台运行）"""
        while self._running and not self._abort_event.is_set():
            try:
                # 更新AI状态
                update_ai_studio_status("researching", f"监控中... {self.stock_codes}")

                # 这里应该调用真实的行情API
                # 简化：模拟检查
                self._check_market()
                self._check_positions()

                time.sleep(5)  # 每5秒检查一次

            except Exception as e:
                task_manager.write_output(self.task_id or "", f"Error: {e}\n")

        # 任务结束
        if self.task_id:
            task_manager.complete(self.task_id)

    def _check_market(self):
        """检查大盘"""
        # 模拟检查
        msg = f"[{datetime.now().strftime('%H:%M:%S')}] 检查大盘...\n"
        if self.task_id:
            task_manager.write_output(self.task_id, msg)
        print(msg.strip())

    def _check_positions(self):
        """检查持仓"""
        state = get_trading_state()
        for code, pos in state.positions.items():
            msg = f"[{datetime.now().strftime('%H:%M:%S')}] {code}: {pos.current_price} ({pos.profit_loss_pct:+.2f}%)\n"
            if self.task_id:
                task_manager.write_output(self.task_id, msg)


# ============================================================================
# Hooks System - 监控钩子
# ============================================================================

class MarketMonitorHook:
    """
    市场监控钩子
    使用Hooks System实现定时监控
    """

    def __init__(self):
        self.hook_id: Optional[str] = None

    def register(self):
        """注册钩子"""
        # 定时检查钩子
        def check_market_hook(input: HookInput) -> dict:
            state = get_monitor_state()
            trading_state = get_trading_state()

            # 检查建仓条件
            can_buy = (
                state.is_stable_above_ma5 and
                state.is_ma5_above_ma10 and
                trading_state.cash >= 10000
            )

            # 检查止损条件
            should_stop_loss = False
            for code, pos in trading_state.positions.items():
                loss_pct = -pos.profit_loss_pct
                if loss_pct >= 8:
                    should_stop_loss = True
                    break

            return {
                "continue": True,
                "additional_context": json.dumps({
                    "index_price": state.index_price,
                    "ma5": state.ma5,
                    "ma10": state.ma10,
                    "can_buy": can_buy,
                    "should_stop_loss": should_stop_loss,
                    "cash": trading_state.cash,
                    "position_count": len(trading_state.positions),
                }, ensure_ascii=False),
            }

        self.hook_id = hooks_manager.add_function_hook(
            event=HookEvent.SESSION_START,
            matcher="*",
            callback=check_market_hook,
            error_message="市场检查钩子失败",
        )
        print(f"[MarketHook] 注册钩子: {self.hook_id}")

    def unregister(self):
        """注销钩子"""
        if self.hook_id:
            hooks_manager.remove_function_hook(
                self.hook_id,
                HookEvent.SESSION_START,
            )
            print(f"[MarketHook] 注销钩子: {self.hook_id}")


# ============================================================================
# Coordinator - 多标的同时分析
# ============================================================================

class TradingCoordinator:
    """
    交易协调器
    使用Coordinator模式并行分析多个标的
    """

    def __init__(self):
        self.coord = Coordinator("蛋蛋交易协调器")
        self.agent = AgentTool(self.coord)
        self.send = SendMessageTool(self.coord)

    def analyze_parallel(self, stock_codes: List[str]) -> dict:
        """
        并行分析多个股票
        返回：各标的研究结果
        """
        update_ai_studio_status("researching", f"并行分析 {len(stock_codes)} 个标的")

        # 并行启动研究Worker
        for code in stock_codes:
            self.agent(
                description=f"分析{code}",
                prompt=f"""分析股票 {code}：
1. 获取当前价格和成交量
2. 计算RSI指标
3. 检查是否触及止损位（成本-8%）
4. 检查是否触及止盈位（成本+10%/+15%/+20%）
5. 给出操作建议：买入/持有/卖出/观望

报告格式：
- 当前价格：
- RSI：
- 距离止损位：
- 距离止盈位：
- 操作建议：
""",
            )

        # 等待完成
        time.sleep(3)

        # 综合结果
        results = {}
        for worker in self.coord.completed_workers():
            results[worker.description] = worker.result

        update_ai_studio_status("idle", "分析完成")
        return results

    def make_decision(self, research_results: dict) -> dict:
        """
        根据研究结果做出交易决策
        Coordinator的核心职责：综合分析 → 决策
        """
        update_ai_studio_status("writing", "制定交易计划")

        # 模拟决策逻辑
        decisions = []
        for name, result in research_results.items():
            if "买入" in result:
                decisions.append({"action": "BUY", "stock": name.replace("分析", "")})
            elif "卖出" in result:
                decisions.append({"action": "SELL", "stock": name.replace("分析", "")})
            else:
                decisions.append({"action": "HOLD", "stock": name.replace("分析", "")})

        update_ai_studio_status("idle", "决策完成")
        return {
            "decisions": decisions,
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# 便捷函数
# ============================================================================

def init_trading_system():
    """初始化交易系统"""
    print("=" * 60)
    print("🥚 蛋蛋交易系统初始化")
    print("=" * 60)

    # 注册监控钩子
    market_hook = MarketMonitorHook()
    market_hook.register()

    # 设置状态
    update_ai_studio_status("idle", "系统就绪")

    print("\n✅ 系统初始化完成！")
    return market_hook


def execute_trade_flow(stock_codes: List[str]):
    """
    执行完整交易流程
    演示如何使用四大系统协作
    """
    print("\n" + "=" * 60)
    print("🚀 开始交易流程")
    print("=" * 60)

    # 1. Coordinator: 并行分析
    print("\n📊 阶段1: 并行分析...")
    coord = TradingCoordinator()
    results = coord.analyze_parallel(stock_codes)

    for name, result in results.items():
        print(f"\n[{name}]")
        print(result[:200] if result else "无结果")

    # 2. Coordinator: 制定决策
    print("\n📋 阶段2: 制定决策...")
    decision = coord.make_decision(results)
    print(f"决策: {decision}")

    # 3. Task: 创建看盘任务
    print("\n👁️ 阶段3: 启动看盘任务...")
    monitor = MonitorTask("实时监控", stock_codes)
    task_id = monitor.start()
    print(f"看盘任务ID: {task_id}")

    # 4. Store: 查看状态
    print("\n📦 阶段4: 当前状态...")
    state = trading_store.get_state()
    print(f"AI状态: {state.ai_studio.status}")
    print(f"现金: ¥{state.trading.cash:.2f}")
    print(f"持仓: {len(state.trading.positions)} 只")
    print(f"大盘: {state.monitor.index_name} {state.monitor.index_price}")

    # 停止看盘任务
    time.sleep(2)
    monitor.stop()

    print("\n✅ 交易流程演示完成！")
    return {
        "research": results,
        "decision": decision,
    }


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    # 初始化
    init_trading_system()

    # 演示完整流程
    execute_trade_flow(["600362", "601318", "159892"])

    # 查看最终状态
    print("\n📊 最终状态:")
    print(f"任务统计: {task_manager.stats()}")
    print(f"钩子列表: {hooks_manager._global_hooks}")
