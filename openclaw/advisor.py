"""
Advisor System - 顾问建议系统
基于 Claude Code advisor.ts 设计

顾问工具是一个更强的审查模型，在关键决策点提供建议。
适用于：写代码前、提交前、遇到错误时、考虑改变方法时。
"""
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from .context_cache import memoize_ttl
from .errors import error_message


class AdvisorResultType(Enum):
    """顾问结果类型"""
    ADVISOR_RESULT = "advisor_result"
    ADVISOR_REDACTED_RESULT = "advisor_redacted_result"
    ADVISOR_TOOL_RESULT_ERROR = "advisor_tool_result_error"


@dataclass
class AdvisorBlock:
    """顾问工具调用块"""
    type: str  # 'server_tool_use' or 'advisor_tool_result'
    id: str = ""
    name: str = "advisor"
    input: dict = field(default_factory=dict)
    tool_use_id: str = ""
    content: dict = field(default_factory=dict)


@dataclass
class AdvisorConfig:
    """顾问配置"""
    enabled: bool = False
    can_user_configure: bool = False
    base_model: str = ""
    advisor_model: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "AdvisorConfig":
        return cls(
            enabled=data.get("enabled", False),
            can_user_configure=data.get("canUserConfigure", False),
            base_model=data.get("baseModel", ""),
            advisor_model=data.get("advisorModel", ""),
        )


class Advisor:
    """
    顾问系统 - 在关键决策点提供AI建议
    
    使用场景：
    - 写代码/改代码前
    - 提交前
    - 遇到重复错误时
    - 方法不收敛时
    - 考虑改变方法时
    - 任务完成后宣布完成前
    """
    
    # 顾问工具提示词
    INSTRUCTIONS = """# Advisor Tool

You have access to an `advisor` tool backed by a stronger reviewer model. 
It takes NO parameters -- when you call it, your entire conversation history 
is automatically forwarded. The advisor sees the task, every tool call you've 
made, every result you've seen.

Call advisor BEFORE substantive work -- before writing code, before committing 
to an interpretation, before building on an assumption. If the task requires 
orientation first (finding files, reading code, seeing what's there), do that, 
then call advisor. Orientation is not substantive work. Writing, editing, 
and declaring an answer are.

Also call advisor:
- When you believe the task is complete. BEFORE this call, make your deliverable 
  durable: write the file, stage the change, save the result. The advisor call 
  takes time; if the session ends during it, a durable result persists and 
  an unwritten one doesn't.
- When stuck -- errors recurring, approach not converging, results that don't fit.
- When considering a change of approach.

On tasks longer than a few steps, call advisor at least once before committing 
to an approach and once before declaring done. On short reactive tasks where 
the next action is dictated by tool output you just read, you don't need to 
keep calling -- the advisor adds most of its value on the first call, before 
the approach crystallizes.

Give the advice serious weight. If you follow a step and it fails empirically, 
or you have primary-source evidence that contradicts a specific claim (the file 
says X, the code does Y), adapt. A passing self-test is not evidence the advice 
is wrong -- it's evidence your test doesn't check what the advice is checking.

If you've already retrieved data pointing one way and the advisor points another: 
don't silently switch. Surface the conflict in one more advisor call -- "I found 
X, you suggest Y, which constraint breaks the tie?" The advisor saw your evidence 
but may have underweighted it; a reconcile call is cheaper than committing to 
the wrong branch."""
    
    def __init__(
        self,
        model: str = "claude-opus-4-5-20251120",
        enabled: bool = True,
    ):
        self.enabled = enabled
        self.model = model
        self.call_history: list[dict] = []
        self._config = AdvisorConfig(enabled=enabled)
    
    def is_enabled(self) -> bool:
        """检查顾问是否启用"""
        return self.enabled
    
    def can_user_configure(self) -> bool:
        """用户是否可以配置顾问"""
        return self._config.can_user_configure
    
    def supports_model(self, model: str) -> bool:
        """检查模型是否支持顾问工具"""
        m = model.lower()
        return (
            "opus-4-6" in m or
            "sonnet-4-6" in m or
            True  # 本地实现默认支持所有模型
        )
    
    def is_valid_advisor_model(self, model: str) -> bool:
        """检查模型是否可以作为顾问模型"""
        m = model.lower()
        return (
            "opus-4-6" in m or
            "sonnet-4-6" in m or
            True  # 本地实现默认支持
        )
    
    def create_tool_use_block(self, task_context: dict) -> AdvisorBlock:
        """创建顾问工具调用块"""
        block_id = f"advisor_{int(time.time() * 1000)}"
        return AdvisorBlock(
            type="server_tool_use",
            id=block_id,
            name="advisor",
            input=task_context,
        )
    
    def create_result_block(
        self,
        tool_use_id: str,
        result: str,
        is_redacted: bool = False,
        error_code: str = "",
    ) -> AdvisorBlock:
        """创建顾问结果块"""
        if error_code:
            return AdvisorBlock(
                type="advisor_tool_result",
                tool_use_id=tool_use_id,
                content={
                    "type": "advisor_tool_result_error",
                    "error_code": error_code,
                },
            )
        elif is_redacted:
            return AdvisorBlock(
                type="advisor_tool_result",
                tool_use_id=tool_use_id,
                content={
                    "type": "advisor_redacted_result",
                    "encrypted_content": result,  # 简化处理
                },
            )
        else:
            return AdvisorBlock(
                type="advisor_tool_result",
                tool_use_id=tool_use_id,
                content={
                    "type": "advisor_result",
                    "text": result,
                },
            )
    
    async def call(
        self,
        task: str,
        history: list[dict],
        conversation: list[dict],
        advisor_model: Optional[str] = None,
    ) -> str:
        """
        调用顾问获取建议
        
        Args:
            task: 当前任务描述
            history: 操作历史
            conversation: 完整对话上下文
            advisor_model: 可选的顾问模型
            
        Returns:
            顾问建议文本
        """
        if not self.enabled:
            return "[Advisor is disabled]"
        
        # 记录调用
        call_record = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "history_length": len(history),
            "conversation_length": len(conversation),
        }
        self.call_history.append(call_record)
        
        # 构建上下文
        context = {
            "task": task,
            "recent_actions": history[-5:] if history else [],
            "conversation": conversation,
        }
        
        # 创建工具调用块
        tool_block = self.create_tool_use_block(context)
        
        # 模拟顾问响应（实际应该调用LLM）
        advice = await self._generate_advice(context, advisor_model)
        
        # 创建结果块
        result_block = self.create_result_block(
            tool_use_id=tool_block.id,
            result=advice,
        )
        
        return advice
    
    async def _generate_advice(
        self,
        context: dict,
        model: Optional[str] = None,
    ) -> str:
        """生成顾问建议（实际实现应该调用LLM）"""
        task = context.get("task", "")
        recent = context.get("recent_actions", [])
        
        # 这里应该调用实际的LLM
        # 简化实现：基于上下文生成建议
        suggestions = []
        
        if not recent:
            suggestions.append("Consider starting with orientation - understand the codebase structure first.")
        else:
            suggestions.append("Good progress. Before making changes, consider if there are any edge cases to handle.")
        
        suggestions.append("Make your deliverable durable (write files, stage changes) before calling advisor again.")
        suggestions.append("If you encounter errors, note the specific error messages for analysis.")
        
        return "\n".join(suggestions)
    
    def get_usage_stats(self) -> dict:
        """获取顾问使用统计"""
        return {
            "total_calls": len(self.call_history),
            "calls_by_task": len(set(c.get("task", "") for c in self.call_history)),
            "last_call": self.call_history[-1] if self.call_history else None,
        }
    
    def reset(self):
        """重置顾问记录"""
        self.call_history.clear()


# 全局顾问实例
_advisor_instance: Optional[Advisor] = None


def get_advisor() -> Advisor:
    """获取全局顾问实例"""
    global _advisor_instance
    if _advisor_instance is None:
        _advisor_instance = Advisor()
    return _advisor_instance


def is_advisor_enabled() -> bool:
    """检查顾问是否启用"""
    return get_advisor().is_enabled()


async def call_advisor(
    task: str,
    history: list[dict],
    conversation: list[dict],
) -> str:
    """快捷函数：调用顾问"""
    return await get_advisor().call(task, history, conversation)
