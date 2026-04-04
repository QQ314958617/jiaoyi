"""
Agentic Session Search - 智能会话语义搜索
基于 Claude Code agenticSessionSearch.ts 设计

使用LLM进行语义搜索，从会话历史中找到与查询相关的会话。
支持标签、标题、摘要、Git分支等多维度匹配。
"""
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .errors import error_message, log_error


# 搜索限制常量
MAX_TRANSCRIPT_CHARS = 2000  # 每个会话的最大字符数
MAX_MESSAGES_TO_SCAN = 100   # 扫描的最大消息数
MAX_SESSIONS_TO_SEARCH = 100 # 发送给API的最大会话数


# 系统提示词
SESSION_SEARCH_SYSTEM_PROMPT = """Your goal is to find relevant sessions based on a user's search query.

You will be given a list of sessions with their metadata and a search query. 
Identify which sessions are most relevant to the query.

Each session may include:
- Title (display name or custom title)
- Tag (user-assigned category, shown as [tag: name] - users tag sessions with /tag command to categorize them)
- Branch (git branch name, shown as [branch: name])
- Summary (AI-generated summary)
- First message (beginning of the conversation)
- Transcript (excerpt of conversation content)

IMPORTANT: Tags are user-assigned labels that indicate the session's topic or category. 
If the query matches a tag exactly or partially, those sessions should be highly prioritized.

For each session, consider (in order of priority):
1. Exact tag matches (highest priority - user explicitly categorized this session)
2. Partial tag matches or tag-related terms
3. Title matches (custom titles or first message content)
4. Branch name matches
5. Summary and transcript content matches
6. Semantic similarity and related concepts

CRITICAL: Be VERY inclusive in your matching. Include sessions that:
- Contain the query term anywhere in any field
- Are semantically related to the query (e.g., "testing" matches sessions about "tests", "unit tests", "QA", etc.)
- Discuss topics that could be related to the query
- Have transcripts that mention the concept even in passing

When in doubt, INCLUDE the session. It's better to return too many results than too few. 
The user can easily scan through results, but missing relevant sessions is frustrating.

Return sessions ordered by relevance (most relevant first). If truly no sessions have ANY 
connection to the query, return an empty array - but this should be rare.

Respond with ONLY the JSON object, no markdown formatting:
{"relevant_indices": [2, 5, 0]}"""


@dataclass
class SessionMetadata:
    """会话元数据"""
    session_id: str
    title: str = ""
    custom_title: str = ""
    tag: str = ""
    git_branch: str = ""
    summary: str = ""
    first_prompt: str = ""
    messages: list[dict] = field(default_factory=list)
    created_at: str = ""
    
    def get_display_title(self) -> str:
        """获取显示标题"""
        if self.custom_title:
            return self.custom_title
        if self.title:
            return self.title
        if self.first_prompt:
            return self.first_prompt[:100] + ("..." if len(self.first_prompt) > 100 else "")
        return "Untitled Session"
    
    def to_search_dict(self, index: int) -> dict:
        """转换为搜索字典"""
        parts = [f"{index}:"]
        parts.append(self.get_display_title())
        
        if self.custom_title and self.custom_title != self.get_display_title():
            parts.append(f"[custom title: {self.custom_title}]")
        
        if self.tag:
            parts.append(f"[tag: {self.tag}]")
        
        if self.git_branch:
            parts.append(f"[branch: {self.git_branch}]")
        
        if self.summary:
            parts.append(f"- Summary: {self.summary}")
        
        if self.first_prompt and self.first_prompt != "No prompt":
            parts.append(f"- First message: {self.first_prompt[:300]}")
        
        # 添加转录摘录
        transcript = self.extract_transcript()
        if transcript:
            parts.append(f"- Transcript: {transcript}")
        
        return {"index": index, "text": "\n".join(parts)}
    
    def extract_transcript(self) -> str:
        """提取转录文本"""
        if not self.messages:
            return ""
        
        # 从头尾各取一半消息
        messages_to_scan = self.messages
        if len(messages_to_scan) > MAX_MESSAGES_TO_SCAN:
            half = MAX_MESSAGES_TO_SCAN // 2
            messages_to_scan = (
                messages_to_scan[:half] + 
                messages_to_scan[-half:]
            )
        
        text_parts = []
        for msg in messages_to_scan:
            text = self._extract_message_text(msg)
            if text:
                text_parts.append(text)
        
        text = " ".join(text_parts).replace(r"\s+", " ").strip()
        
        if len(text) > MAX_TRANSCRIPT_CHARS:
            return text[:MAX_TRANSCRIPT_CHARS] + "…"
        return text
    
    def _extract_message_text(self, message: dict) -> str:
        """从消息中提取文本"""
        msg_type = message.get("type", "")
        if msg_type not in ("user", "assistant"):
            return ""
        
        content = message.get("message", {}).get("content", "")
        if not content:
            return ""
        
        if isinstance(content, str):
            return content
        
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("text"):
                    parts.append(block["text"])
            return " ".join(parts)
        
        return ""
    
    def contains_query(self, query_lower: str) -> bool:
        """检查会话是否包含查询词"""
        # 检查标题
        if query_lower in self.get_display_title().lower():
            return True
        
        # 检查自定义标题
        if self.custom_title and query_lower in self.custom_title.lower():
            return True
        
        # 检查标签
        if self.tag and query_lower in self.tag.lower():
            return True
        
        # 检查分支
        if self.git_branch and query_lower in self.git_branch.lower():
            return True
        
        # 检查摘要
        if self.summary and query_lower in self.summary.lower():
            return True
        
        # 检查首条消息
        if self.first_prompt and query_lower in self.first_prompt.lower():
            return True
        
        # 检查转录（最耗时，放最后）
        transcript = self.extract_transcript().lower()
        if query_lower in transcript:
            return True
        
        return False


@dataclass 
class SearchResult:
    """搜索结果"""
    session: SessionMetadata
    relevance_score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)


class AgenticSearchEngine:
    """
    智能会话搜索引擎
    
    使用LLM进行语义搜索，从大量会话历史中找到与查询相关的会话。
    支持：
    - 标签精确/部分匹配
    - 标题匹配
    - Git分支匹配
    - 摘要和转录内容匹配
    - 语义相似性
    """
    
    def __init__(self, llm_client: Optional[callable] = None):
        """
        Args:
            llm_client: LLM客户端函数，签名: (messages, system) -> str
        """
        self.llm_client = llm_client or self._default_llm_client
        self._search_cache: dict[str, list[SessionMetadata]] = {}
    
    async def _default_llm_client(
        self, 
        messages: list[dict], 
        system: str
    ) -> str:
        """默认LLM客户端（简化实现）"""
        # 这里应该接入实际的LLM
        # 简化：基于关键词匹配返回结果
        query = ""
        for msg in messages:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and "Search query:" in content:
                    # 提取查询
                    match = re.search(r'Search query: "(.*?)"', content, re.DOTALL)
                    if match:
                        query = match.group(1)
        
        return json.dumps({"relevant_indices": []})
    
    async def search(
        self,
        query: str,
        sessions: list[SessionMetadata],
        signal: Optional[Any] = None,
    ) -> list[SessionMetadata]:
        """
        搜索相关会话
        
        Args:
            query: 搜索查询
            sessions: 会话列表
            signal: 中断信号
            
        Returns:
            按相关性排序的会话列表
        """
        if not query.strip() or not sessions:
            return []
        
        query_lower = query.lower()
        
        # 预过滤：找到包含查询词的会话
        matching_sessions = [
            (i, s) for i, s in enumerate(sessions)
            if s.contains_query(query_lower)
        ]
        
        # 如果匹配数超过限制，取前MAX_SESSIONS_TO_SEARCH个
        # 如果匹配数不足，用非匹配会话填充
        logs_to_search: list[tuple[int, SessionMetadata]]
        if len(matching_sessions) >= MAX_SESSIONS_TO_SEARCH:
            logs_to_search = matching_sessions[:MAX_SESSIONS_TO_SEARCH]
        else:
            remaining = MAX_SESSIONS_TO_SEARCH - len(matching_sessions)
            non_matching = [
                (i, s) for i, s in enumerate(sessions)
                if not s.contains_query(query_lower)
            ]
            logs_to_search = matching_sessions + non_matching[:remaining]
        
        # 构建会话列表字符串
        session_list = []
        for idx, session in logs_to_search:
            search_dict = session.to_search_dict(idx)
            session_list.append(search_dict["text"])
        
        session_list_text = "\n".join(session_list)
        
        user_message = f"""Sessions:
{session_list_text}

Search query: "{query}"

Find the sessions that are most relevant to this query."""

        try:
            # 调用LLM进行语义搜索
            response = await self.llm_client(
                messages=[{"role": "user", "content": user_message}],
                system=SESSION_SEARCH_SYSTEM_PROMPT,
            )
            
            # 解析JSON响应
            relevant_indices = self._parse_response(response)
            
            # 映射回原始会话
            index_to_session = {idx: session for idx, session in logs_to_search}
            results = []
            seen = set()
            
            for idx in relevant_indices:
                if 0 <= idx < len(logs_to_search) and idx not in seen:
                    results.append(logs_to_search[idx][1])
                    seen.add(idx)
            
            return results
            
        except Exception as e:
            log_error(e)
            # 回退：返回基于关键词匹配的简单结果
            return [s for _, s in matching_sessions[:10]]
    
    def _parse_response(self, response: str) -> list[int]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group(0))
                indices = data.get("relevant_indices", [])
                return [int(i) for i in indices if str(i).isdigit()]
        except (json.JSONDecodeError, ValueError) as e:
            log_error(f"Failed to parse search response: {e}")
        
        return []
    
    def search_sync(
        self,
        query: str,
        sessions: list[SessionMetadata],
    ) -> list[SessionMetadata]:
        """同步版本搜索"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.search(query, sessions))


# 便捷函数
async def agentic_session_search(
    query: str,
    sessions: list[dict],
) -> list[dict]:
    """
    快捷函数：智能搜索会话
    
    Args:
        query: 搜索查询
        sessions: 会话列表（字典格式）
        
    Returns:
        相关的会话列表
    """
    # 转换字典到SessionMetadata
    session_objects = [
        SessionMetadata(
            session_id=s.get("session_id", str(i)),
            title=s.get("title", ""),
            custom_title=s.get("customTitle", ""),
            tag=s.get("tag", ""),
            git_branch=s.get("gitBranch", ""),
            summary=s.get("summary", ""),
            first_prompt=s.get("firstPrompt", ""),
            messages=s.get("messages", []),
            created_at=s.get("createdAt", ""),
        )
        for i, s in enumerate(sessions)
    ]
    
    engine = AgenticSearchEngine()
    results = await engine.search(query, session_objects)
    
    # 转换回字典
    return [
        {
            "session_id": r.session_id,
            "title": r.title,
            "custom_title": r.custom_title,
            "tag": r.tag,
            "git_branch": r.git_branch,
            "summary": r.summary,
            "first_prompt": r.first_prompt,
            "created_at": r.created_at,
        }
        for r in results
    ]


# 导出
__all__ = [
    "AgenticSearchEngine",
    "AgenticSearchEngine",
    "SessionMetadata",
    "SearchResult",
    "agentic_session_search",
    "SESSION_SEARCH_SYSTEM_PROMPT",
]
