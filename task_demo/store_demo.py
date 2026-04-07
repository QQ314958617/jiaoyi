"""
State Store Demo - 状态存储演示
展示如何用于AI工作室状态同步
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from store import Store, create_store


# ============================================================================
# 蛋蛋的交易系统状态
# ============================================================================

@dataclass
class TradingState:
    """交易系统状态"""
    cash: float = 50000.0          # 现金
    positions: Dict[str, dict] = field(default_factory=dict)  # 持仓 {code: {shares, cost}}
    total_value: float = 50000.0    # 总市值
    daily_pnl: float = 0.0         # 今日盈亏


@dataclass
class AIStudioState:
    """AI工作室状态"""
    status: str = "idle"            # researching | writing | executing | syncing | idle | error
    description: str = ""
    current_task: Optional[str] = None
    last_update: str = ""


@dataclass
class MarketState:
    """市场状态"""
    index: str = "000001"           # 指数代码
    name: str = "上证指数"
    price: float = 0.0
    change_pct: float = 0.0
    ma5: float = 0.0
    ma10: float = 0.0
    timestamp: str = ""


@dataclass
class AppState:
    """全局应用状态"""
    trading: TradingState = field(default_factory=TradingState)
    ai_studio: AIStudioState = field(default_factory=AIStudioState)
    market: MarketState = field(default_factory=MarketState)
    session_id: str = ""
    debug_mode: bool = False


# ============================================================================
# 全局状态存储
# ============================================================================

app_store = create_store(AppState())


# ============================================================================
# 演示函数
# ============================================================================

def demo_basic_state():
    """演示基本状态操作"""
    print("=== 基本状态操作 ===\n")

    # 获取状态
    state = app_store.get_state()
    print(f"当前状态: status={state.ai_studio.status}, cash={state.trading.cash}")

    # 更新状态（函数式）
    app_store.set_state(lambda s: AppState(
        **{
            **s.__dict__,
            "trading": TradingState(
                **{
                    **s.trading.__dict__,
                    "cash": s.trading.cash - 5000
                }
            )
        }
    ))
    print(f"更新后: cash={app_store.get_state().trading.cash}")


def demo_subscriber():
    """演示订阅机制"""
    print("\n=== 订阅机制演示 ===\n")

    update_count = {"value": 0}

    def on_status_change():
        update_count["value"] += 1
        state = app_store.get_state()
        print(f"[订阅#{update_count['value']}] 状态变为: {state.ai_studio.status}")

    # 订阅状态变更
    unsubscribe = app_store.subscribe(on_status_change)

    # 多次更新
    app_store.set_state(lambda s: AppState(
        **{
            **s.__dict__,
            "ai_studio": AIStudioState(
                status="researching",
                description="分析市场数据"
            )
        }
    ))

    app_store.set_state(lambda s: AppState(
        **{
            **s.__dict__,
            "ai_studio": AIStudioState(
                status="executing",
                description="执行交易"
            )
        }
    ))

    # 取消订阅
    unsubscribe()

    # 这次不会触发订阅
    app_store.set_state(lambda s: AppState(
        **{
            **s.__dict__,
            "ai_studio": AIStudioState(
                status="idle",
                description=""
            )
        }
    ))

    print(f"\n订阅收到 {update_count['value']} 次更新（取消订阅后2次未收到）")


def demo_selector():
    """演示选择器模式（只关心特定字段）"""
    print("\n=== 选择器模式演示 ===\n")

    def create_selector(field_path: str) -> Callable:
        """创建选择器函数"""
        def selector(state: AppState) -> any:
            parts = field_path.split(".")
            value = state
            for part in parts:
                value = getattr(value, part)
            return value
        return selector

    status_selector = create_selector("ai_studio.status")
    cash_selector = create_selector("trading.cash")

    print(f"当前状态: status={status_selector(app_store.get_state())}")
    print(f"当前现金: cash={cash_selector(app_store.get_state())}")


def demo_trading_workflow():
    """演示交易工作流状态变化"""
    print("\n=== 交易工作流演示 ===\n")

    # 模拟完整的交易流程
    workflow = [
        ("researching", "检查大盘指数..."),
        ("researching", "分析标的股票..."),
        ("idle", ""),  # 暂时空闲
        ("researching", "等待买入时机..."),
        ("idle", ""),
        ("executing", "买入 600362 100股"),
        ("syncing", "同步交易记录..."),
        ("idle", ""),
    ]

    for status, desc in workflow:
        app_store.set_state(lambda s: AppState(
            **{
                **s.__dict__,
                "ai_studio": AIStudioState(
                    status=status,
                    description=desc
                )
            }
        ))
        state = app_store.get_state()
        print(f"[{state.ai_studio.status}] {state.ai_studio.description or '(无描述)'}")

    print("\n交易流程完成！")


def demo_thread_safety():
    """演示线程安全"""
    import threading
    import time

    print("\n=== 线程安全演示 ===\n")

    results = {"counter": 0}
    lock = threading.Lock()

    def increment_many_times():
        for _ in range(100):
            app_store.set_state(lambda s: AppState(
                **{
                    **s.__dict__,
                    "trading": TradingState(
                        cash=s.trading.cash + 1
                    )
                }
            ))
            with lock:
                results["counter"] += 1

    # 启动10个线程同时更新状态
    threads = [threading.Thread(target=increment_many_times) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"执行 {results['counter']} 次更新")
    print(f"最终现金: {app_store.get_state().trading.cash}")


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    demo_basic_state()
    demo_subscriber()
    demo_selector()
    demo_trading_workflow()
    demo_thread_safety()
    print("\n✅ 状态存储演示完成！")
