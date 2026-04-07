"""
Hooks System Demo - 钩子系统演示
"""
from hooks_base import HookEvent, HookInput, HookConfig, HookType, HookOutput
from hooks_manager import hooks_manager, HooksManager


def demo_basic_hooks():
    """演示基本钩子功能"""
    print("=== 基本钩子演示 ===\n")

    # 创建钩子输入
    hook_input = HookInput(
        hook_event_name=HookEvent.PRE_TOOL_USE,
        session_id="demo-session-001",
        cwd="/root",
        tool_name="bash",
        tool_input={"command": "echo hello"},
    )

    # 注册一个函数钩子
    def my_pre_tool_hook(input: HookInput) -> dict:
        print(f"[钩子触发] 事件: {input.hook_event_name}")
        print(f"[钩子触发] 工具: {input.tool_name}")
        print(f"[钩子触发] 输入: {input.tool_input}")
        return {"continue": True}

    hook_id = hooks_manager.add_function_hook(
        event=HookEvent.PRE_TOOL_USE,
        matcher="bash",
        callback=my_pre_tool_hook,
        error_message="Hook failed",
    )
    print(f"注册钩子 ID: {hook_id}")

    # 触发钩子
    print("\n触发 PreToolUse:bash 钩子...")
    results = hooks_manager.fire(HookEvent.PRE_TOOL_USE, hook_input)
    print(f"执行结果: {[r.to_dict() for r in results]}")

    # 清理
    hooks_manager.remove_function_hook(hook_id, HookEvent.PRE_TOOL_USE)
    print("\n钩子已删除")


def demo_session_hooks():
    """演示会话级钩子"""
    print("\n=== 会话级钩子演示 ===\n")

    session_id = "temp-session-123"

    # 创建会话
    hooks_manager.create_session(session_id)
    print(f"创建会话: {session_id}")

    # 注册会话级钩子
    def on_session_start(input: HookInput):
        print(f"[会话开始] session_id={input.session_id}, cwd={input.cwd}")
        return True

    def on_session_end(input: HookInput):
        print(f"[会话结束] session_id={input.session_id}")
        return True

    hooks_manager.on_session_start(on_session_start, session_id)
    hooks_manager.on_session_end(on_session_end, session_id)

    # 触发会话开始
    print("\n触发会话开始...")
    start_input = HookInput(
        hook_event_name=HookEvent.SESSION_START,
        session_id=session_id,
        cwd="/root/.openclaw/workspace",
    )
    hooks_manager.fire(HookEvent.SESSION_START, start_input, session_id)

    # 触发会话结束
    print("\n触发会话结束...")
    end_input = HookInput(
        hook_event_name=HookEvent.SESSION_END,
        session_id=session_id,
        cwd="/root/.openclaw/workspace",
    )
    hooks_manager.fire(HookEvent.SESSION_END, end_input, session_id)

    # 销毁会话
    hooks_manager.destroy_session(session_id)
    print("\n会话已销毁")


def demo_command_hook():
    """演示命令类型钩子"""
    print("\n=== 命令类型钩子演示 ===\n")

    # 注册一个命令钩子（简单echo）
    config = HookConfig(
        id="cmd-hook-001",
        name="测试命令钩子",
        hook_type=HookType.COMMAND,
        event=HookEvent.SESSION_START,
        matcher="*",
        command='echo \'{"continue": true, "reason": "command hook worked"}\'',
    )
    hooks_manager.register_hook(config)

    # 触发
    hook_input = HookInput(
        hook_event_name=HookEvent.SESSION_START,
        session_id="cmd-demo",
        cwd="/root",
    )
    results = hooks_manager.fire(HookEvent.SESSION_START, hook_input)
    print(f"命令钩子结果: {results[0].to_dict() if results else 'no results'}")


def demo_trading_hooks():
    """演示交易场景的钩子"""
    print("\n=== 交易场景钩子演示 ===\n")

    session_id = "trading-session"

    # 1. 交易前检查 - 检查大盘是否站稳5日线
    def check_market_before_trade(input: HookInput) -> dict:
        # 实际应该调用API检查大盘
        print("[交易前检查] 检查大盘指数...")
        # 模拟返回：允许交易
        return {
            "continue": True,
            "additional_context": "大盘站稳5日线，可以交易",
        }

    # 2. 交易后通知
    def notify_after_trade(input: HookInput) -> dict:
        print(f"[交易完成] 工具: {input.tool_name}")
        print(f"[交易完成] 输入: {input.tool_input}")
        return {"continue": True}

    # 注册钩子
    hooks_manager.add_function_hook(
        HookEvent.PRE_TOOL_USE,
        "trade",
        check_market_before_trade,
        "交易前检查失败",
        session_id,
    )
    hooks_manager.add_function_hook(
        HookEvent.POST_TOOL_USE,
        "trade",
        notify_after_trade,
        "交易通知失败",
        session_id,
    )

    # 模拟交易前检查
    print("--- 模拟交易前检查 ---")
    pre_input = HookInput(
        hook_event_name=HookEvent.PRE_TOOL_USE,
        session_id=session_id,
        cwd="/root",
        tool_name="trade",
        tool_input={"action": "buy", "stock": "600362", "shares": 100},
    )
    results = hooks_manager.fire(HookEvent.PRE_TOOL_USE, pre_input, session_id)
    print(f"结果: {results[0].to_dict() if results else 'blocked'}")

    # 模拟交易后通知
    print("\n--- 模拟交易完成通知 ---")
    post_input = HookInput(
        hook_event_name=HookEvent.POST_TOOL_USE,
        session_id=session_id,
        cwd="/root",
        tool_name="trade",
        tool_input={"action": "buy", "stock": "600362", "shares": 100},
    )
    hooks_manager.fire(HookEvent.POST_TOOL_USE, post_input, session_id)


if __name__ == "__main__":
    demo_basic_hooks()
    demo_session_hooks()
    demo_command_hook()
    demo_trading_hooks()
    print("\n✅ 所有演示完成！")
