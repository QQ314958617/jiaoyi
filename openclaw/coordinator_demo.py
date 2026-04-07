"""
Coordinator Demo - 多Agent协调器演示
展示如何用Coordinator协调多个Worker并行工作
"""
import time
from coordinator import (
    Coordinator,
    AgentTool,
    SendMessageTool,
    WorkerStatus,
)


def demo_basic_coordinator():
    """演示基本协调器功能"""
    print("=== 基本协调器演示 ===\n")

    # 创建协调器
    coord = Coordinator("主协调者")

    # 注册回调
    def on_worker_complete(worker):
        print(f"[回调] Worker完成: {worker.description}, 耗时: {worker.duration_ms()}ms")

    coord.on("worker_completed", on_worker_complete)

    # 使用AgentTool启动Worker
    agent = AgentTool(coord)

    # 并行启动两个Worker研究不同问题
    result1 = agent(
        description="研究认证模块",
        prompt="研究src/auth/目录下的认证逻辑，找出可能的安全漏洞。报告文件路径和具体问题。",
    )
    print(f"启动Worker1: {result1}")

    result2 = agent(
        description="研究支付模块",
        prompt="研究src/payment/目录下的支付逻辑，找出可能的风险点。报告文件路径和具体问题。",
    )
    print(f"启动Worker2: {result2}")

    # 等待Worker完成
    print("\n等待Worker完成...")
    time.sleep(2)

    # 查看结果
    print("\n--- Worker结果 ---")
    for worker in coord.completed_workers():
        print(f"\n[{worker.description}]")
        print(worker.result)

    print(f"\n总日志条数: {len(coord.get_log())}")


def demo_research_synthesis():
    """
    演示研究-综合工作流
    这是Claude Code推荐的核心工作流
    """
    print("\n=== 研究-综合工作流演示 ===\n")

    coord = Coordinator("蛋蛋")

    # 第一阶段：并行研究
    print("阶段1: 并行研究...")
    agent = AgentTool(coord)

    # 启动多个研究Worker
    agent(description="研究大盘指数MA5/MA10状态", prompt="""
研究当前大盘指数的状态：
1. 检查MA5是否上穿/下穿MA10
2. 检查指数是否站稳5日线
3. 检查成交量是否放大
报告具体数值和建议。
""")

    agent(description="研究持仓股票状态", prompt="""
研究以下持仓股票的状态：
- 600362 江西铜业
- 601318 中国平安
报告每只股票的RSI、成交量变化、是否触及止损止盈位。
""")

    agent(description="研究市场情绪", prompt="""
研究当前市场情绪：
1. 涨跌停数量
2. 主力资金流向
3. 板块轮动情况
报告具体数据和情绪判断。
""")

    # 等待研究完成
    print("等待研究Worker完成...")
    time.sleep(3)

    # 第二阶段：综合分析
    print("\n阶段2: 综合分析...")
    synthesis = coord.synthesize_results()
    print("\n综合分析结果:")
    print(synthesis)

    # 第三阶段：根据研究结果继续Worker执行
    print("\n阶段3: 继续Worker执行...")
    send = SendMessageTool(coord)

    # 继续第一个Worker，让它执行具体任务
    workers = coord.completed_workers()
    if workers:
        send(to=workers[0].id, message="""
基于你的研究结果，执行以下操作：
1. 如果MA5上穿MA10且指数站稳5日线，准备买入信号
2. 如果MA5下穿MA10，准备卖出信号
报告具体的操作计划。
""")


def demo_stop_and_continue():
    """演示停止和继续Worker"""
    print("\n=== 停止和继续Worker演示 ===\n")

    coord = Coordinator("测试协调器")
    agent = AgentTool(coord)
    send = SendMessageTool(coord)

    # 启动一个Worker
    result = agent(
        description="实现JWT认证",
        prompt="将现有session认证重构为JWT认证...",
    )
    worker_id = result["task_id"]
    print(f"启动Worker: {worker_id}")

    # 模拟用户改变了需求
    print("\n用户改变需求：'不要重构了，只修一个null pointer bug'")
    print("停止当前Worker...")

    # 停止Worker
    coord.stop(worker_id)
    print(f"Worker状态: {coord.get_worker(worker_id).status}")

    # 启动新的Worker做正确的事
    print("\n启动新的Worker做正确的任务...")
    result2 = agent(
        description="修复null pointer",
        prompt="修复src/auth/validate.ts:42的null pointer bug...",
    )
    print(f"新Worker: {result2}")

    time.sleep(1.5)

    # 查看最终状态
    print("\n--- 最终状态 ---")
    for worker in coord.list_workers():
        print(f"{worker.description}: {worker.status.value}")


def demo_notification_format():
    """演示task-notification格式"""
    print("\n=== Task Notification格式演示 ===\n")

    coord = Coordinator("通知测试")

    # 注册通知处理
    def on_notification(notif):
        print(f"\n收到通知:")
        print(f"  task_id: {notif.get('task_id')}")
        print(f"  status: {notif.get('status')}")
        print(f"  summary: {notif.get('summary')}")

    coord.on("notification", on_notification)

    # 模拟收到通知
    notification = """
<task-notification>
<task-id>agent-a1b2c3d4</task-id>
<status>completed</status>
<summary>Agent "研究认证模块" completed</summary>
<result>发现问题：validate.ts:42 缺少null check
建议：添加 if (!user) return 401</result>
</task-notification>
""".strip()

    # 解析通知（简化版）
    import re
    task_id = re.search(r'<task-id>(.*?)</task-id>', notification).group(1)
    status = re.search(r'<status>(.*?)</status>', notification).group(1)
    summary = re.search(r'<summary>(.*?)</summary>', notification).group(1)
    result = re.search(r'<result>(.*?)</result>', notification, re.DOTALL)

    coord.on_notification({
        "task_id": task_id,
        "status": status,
        "summary": summary,
        "result": result.group(1) if result else "",
    })

    print("\n处理后的Worker状态:")
    worker = coord.get_worker(task_id)
    print(f"  状态: {worker.status}")
    print(f"  结果: {worker.result[:50] if worker.result else 'N/A'}...")


if __name__ == "__main__":
    demo_basic_coordinator()
    demo_research_synthesis()
    demo_stop_and_continue()
    demo_notification_format()
    print("\n✅ Coordinator演示完成！")
