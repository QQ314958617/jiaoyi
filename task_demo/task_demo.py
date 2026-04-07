"""
Task System 示例和测试
"""
from task_manager import task_manager, TaskState
from task_base import TaskType, TaskStatus
from task_bash import run_bash, run_bash_bg


def demo_task_lifecycle():
    """演示任务生命周期"""
    print("=== 任务生命周期演示 ===\n")

    # 1. 创建任务
    task = task_manager.create_task(
        TaskType.LOCAL_BASH,
        "测试命令",
        tool_use_id="test-001",
    )
    print(f"创建任务: {task.id}, 状态: {task.status.value}")

    # 2. 启动任务
    task_manager.start(task.id)
    print(f"启动任务: {task.id}, 状态: {task.status.value}")

    # 3. 更新任务
    task_manager.update(task.id, lambda t: t.__class__(
        **{
            **t.__dict__,
            "extra": {"progress": 50}
        }
    ))
    print(f"更新任务: {task.id}, extra: {task_manager.get(task.id).extra}")

    # 4. 完成任务
    task_manager.complete(task.id)
    print(f"完成任务: {task.id}, 状态: {task.status.value}")
    print(f"耗时: {task_manager.get(task.id).duration_ms()}ms")


def demo_callbacks():
    """演示回调机制"""
    print("\n=== 回调机制演示 ===\n")

    def on_complete(task):
        print(f"[回调] 任务完成: {task.id}")

    def on_fail(task):
        print(f"[回调] 任务失败: {task.id}")

    task_manager.on_complete(on_complete)
    task_manager.on_fail(on_fail)

    # 创建并完成任务
    task = task_manager.create_task(TaskType.LOCAL_BASH, "回调测试")
    task_manager.complete(task.id)


def demo_bash_task():
    """演示Bash任务"""
    print("\n=== Bash任务演示 ===\n")

    # 同步执行
    print("执行: echo 'hello'")
    exit_code, output = run_bash("echo 'hello from task system'", timeout=5000)
    print(f"退出码: {exit_code}, 输出: {output.strip()}")

    # 后台执行
    print("\n执行后台任务: sleep 2 && echo 'done'")
    task_id = run_bash_bg("sleep 1 && echo 'background task done'")
    print(f"后台任务ID: {task_id}")

    # 检查状态
    import time
    time.sleep(2)
    task = task_manager.get(task_id)
    if task:
        print(f"任务状态: {task.status.value}")


def demo_stats():
    """演示统计信息"""
    print("\n=== 统计信息 ===\n")
    print(f"任务统计: {task_manager.stats()}")


if __name__ == "__main__":
    demo_task_lifecycle()
    demo_callbacks()
    demo_bash_task()
    demo_stats()
