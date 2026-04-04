"""
Side Query - 边查询API封装
基于 Claude Code sideQuery.ts 设计

轻量级API封装，用于在主对话循环之外发起"边查询"。
确保正确的OAuth令牌验证和指纹归属头。
"""
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .errors import error_message


@dataclass
class SideQueryOptions:
    """
    边查询选项
    
    Attributes:
        model: 要使用的模型
        system: 系统提示词
        messages: 发送的消息列表
        tools: 可选的工具列表
        tool_choice: 可选的工具选择
        output_format: 结构化输出格式
        max_tokens: 最大token数 (默认1024)
        max_retries: 最大重试次数 (默认2)
        signal: 中断信号
        skip_system_prompt_prefix: 跳过CLI系统提示词前缀
        temperature: 温度参数
        thinking: 思考预算
        stop_sequences: 停止序列
        query_source: 查询来源标识
    """
    model: str
    messages: list
    system: Optional[str | list] = None
    tools: Optional[list] = None
    tool_choice: Optional[dict] = None
    output_format: Optional[dict] = None
    max_tokens: int = 1024
    max_retries: int = 2
    signal: Optional[Any] = None
    skip_system_prompt_prefix: bool = False
    temperature: Optional[float] = None
    thinking: Optional[int | bool] = None
    stop_sequences: Optional[list[str]] = None
    query_source: str = "side_query"


@dataclass
class ApiResponse:
    """
    API响应
    
    Attributes:
        content: 响应内容块列表
        usage: Token使用统计
        id: 请求ID
        model: 实际使用的模型
        type: 响应类型
    """
    content: list = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    id: str = ""
    model: str = ""
    type: str = "message"
    
    @classmethod
    def from_dict(cls, data: dict) -> "ApiResponse":
        return cls(
            content=data.get("content", []),
            usage=data.get("usage", {}),
            id=data.get("id", ""),
            model=data.get("model", ""),
            type=data.get("type", "message"),
        )


@dataclass
class TokenUsage:
    """Token使用统计"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


class SideQueryClient:
    """
    边查询客户端
    
    用于在主对话循环之外发起轻量级API查询。
    适用于：
    - 权限解释器
    - 会话搜索
    - 模型验证
    - 其他辅助任务
    """
    
    def __init__(self, api_client: Optional[callable] = None):
        """
        Args:
            api_client: API客户端函数，签名为 (model, messages, system, tools, **kwargs) -> Response
        """
        self.api_client = api_client or self._default_api_client
        self._last_completion_timestamp: Optional[float] = None
    
    async def _default_api_client(
        self,
        model: str,
        messages: list,
        **kwargs,
    ) -> dict:
        """
        默认API客户端（简化实现）
        
        实际应该调用Anthropic API
        """
        # 这里应该实现实际的API调用
        # 简化：返回一个模拟响应
        return {
            "id": f"side_{int(time.time() * 1000)}",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": [
                {"type": "text", "text": "Side query result"}
            ],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
            }
        }
    
    @staticmethod
    def extract_first_user_message_text(messages: list[dict]) -> str:
        """
        从消息列表中提取第一个用户消息的文本
        
        Args:
            messages: 消息列表
            
        Returns:
            第一个用户消息的文本内容
        """
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            return block.get("text", "")
        return ""
    
    @staticmethod
    def compute_fingerprint(text: str, version: str) -> str:
        """
        计算指纹用于OAuth验证
        
        Args:
            text: 文本内容
            version: 版本字符串
            
        Returns:
            指纹字符串
        """
        import hashlib
        combined = f"{text}:{version}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    async def query(self, opts: SideQueryOptions) -> ApiResponse:
        """
        执行边查询
        
        Args:
            opts: 查询选项
            
        Returns:
            API响应
        """
        # 构建系统提示词块
        system_blocks = []
        
        # 添加归属头
        fingerprint = self.compute_fingerprint(
            self.extract_first_user_message_text(opts.messages),
            "1.0",  # 版本号
        )
        attribution = f"[Attribution: claude-code {fingerprint}]"
        system_blocks.append({"type": "text", "text": attribution})
        
        # 添加CLI系统提示词前缀（除非跳过）
        if not opts.skip_system_prompt_prefix:
            cli_prefix = "You are Claude Code, an AI assistant."
            system_blocks.append({"type": "text", "text": cli_prefix})
        
        # 添加用户提供的系统提示词
        if opts.system:
            if isinstance(opts.system, str):
                system_blocks.append({"type": "text", "text": opts.system})
            elif isinstance(opts.system, list):
                system_blocks.extend(opts.system)
        
        # 构建请求参数
        request_kwargs = {
            "model": opts.model,
            "max_tokens": opts.max_tokens,
            "system": system_blocks,
            "messages": opts.messages,
        }
        
        # 添加可选参数
        if opts.tools:
            request_kwargs["tools"] = opts.tools
        
        if opts.tool_choice:
            request_kwargs["tool_choice"] = opts.tool_choice
        
        if opts.output_format:
            request_kwargs["output_config"] = {"format": opts.output_format}
        
        if opts.temperature is not None:
            request_kwargs["temperature"] = opts.temperature
        
        if opts.stop_sequences:
            request_kwargs["stop_sequences"] = opts.stop_sequences
        
        if opts.thinking is not None:
            if opts.thinking is False:
                request_kwargs["thinking"] = {"type": "disabled"}
            elif isinstance(opts.thinking, int):
                request_kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": min(opts.thinking, opts.max_tokens - 1),
                }
        
        # 调用API
        start_time = time.time()
        try:
            response = await self.api_client(**request_kwargs)
        except Exception as e:
            error_message(f"Side query failed: {e}")
            raise
        
        # 记录完成时间
        self._last_completion_timestamp = time.time()
        
        # 计算持续时间
        duration_ms = (time.time() - start_time) * 1000
        
        # 记录日志（如果有analytics）
        # logEvent('tengu_api_success', {...})
        
        return ApiResponse.from_dict(response)
    
    async def permission_explainer(
        self,
        model: str,
        system: str,
        messages: list,
        tools: Optional[list] = None,
    ) -> ApiResponse:
        """
        权限解释器查询
        
        用于解释权限决策
        """
        return await self.query(SideQueryOptions(
            model=model,
            system=system,
            messages=messages,
            tools=tools,
            query_source="permission_explainer",
        ))
    
    async def session_search(
        self,
        model: str,
        search_prompt: str,
        sessions_content: str,
    ) -> ApiResponse:
        """
        会话搜索查询
        
        用于从会话历史中搜索相关内容
        """
        messages = [
            {"role": "user", "content": f"Sessions:\n{sessions_content}\n\nSearch query: {search_prompt}"}
        ]
        
        return await self.query(SideQueryOptions(
            model=model,
            messages=messages,
            query_source="session_search",
        ))
    
    async def model_validation(
        self,
        model: str,
    ) -> ApiResponse:
        """
        模型验证查询
        
        用于验证模型是否可用
        """
        return await self.query(SideQueryOptions(
            model=model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=1,
            query_source="model_validation",
        ))
    
    def get_last_completion_timestamp(self) -> Optional[float]:
        """获取上次API完成的时间戳"""
        return self._last_completion_timestamp


# 全局客户端实例
_side_query_client: Optional[SideQueryClient] = None


def get_side_query_client() -> SideQueryClient:
    """获取全局边查询客户端"""
    global _side_query_client
    if _side_query_client is None:
        _side_query_client = SideQueryClient()
    return _side_query_client


async def side_query(opts: SideQueryOptions) -> ApiResponse:
    """
    快捷函数：执行边查询
    
    Args:
        opts: 查询选项
        
    Returns:
        API响应
    """
    client = get_side_query_client()
    return await client.query(opts)


# 导出
__all__ = [
    "SideQueryOptions",
    "SideQueryClient",
    "ApiResponse",
    "TokenUsage",
    "side_query",
    "get_side_query_client",
]
