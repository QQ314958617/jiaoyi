"""
OpenClaw Prompt Template System
================================
Inspired by Claude Code's src/utils/argumentSubstitution.ts (150+ lines).

核心功能：
1. 变量替换：$variable, $0, $1
2. 命名参数：$stock_code, $strategy
3. 默认值：${variable:default_value}
4. 条件区块：{{#if variable}}...{{/if}}
5. 循环区块：{{#each items}}...{{/each}}
6. Prompt 缓存 + TTL

Claude Code 的设计：
- parseArgumentNames() — 解析参数列表
- substituteArguments() — 替换 $variable 占位符
- generateProgressiveArgumentHint() — 未填充参数提示

我们的扩展：
- 默认值语法：${variable:default}
- 条件区块：{{#if condition}}...{{/if}}
- 循环区块：{{#each list}}...{{/each}}
"""

from __future__ import annotations

import re
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum


# ============================================================================
# 模板解析
# ============================================================================

@dataclass
class TemplateBlock:
    """模板块"""
    kind: str  # "text" | "variable" | "if" | "each" | "else"
    content: str = ""
    variable: str = ""  # for variable/if/each
    default_value: str = ""  # for variable with default
    items_var: str = ""  # for each
    body: List["TemplateBlock"] = field(default_factory=list)  # for if/each


class PromptTemplate:
    """
    Prompt 模板。

    支持：
    - $variable — 命名变量
    - $0, $1 — 位置变量
    - ${variable:default} — 带默认值
    - {{#if condition}}...{{/if}} — 条件区块
    - {{#each list}}...{{/each}} — 循环区块
    """

    def __init__(
        self,
        template: str,
        name: Optional[str] = None,
        description: str = "",
        cache_ttl: float = 300,  # 5 minutes
    ):
        self.name = name or "anonymous"
        self.description = description
        self.template = template
        self._cache_ttl = cache_ttl
        self._compiled: Optional[List[TemplateBlock]] = None
        self._cache: Dict[str, Tuple[str, float]] = {}  # cache_key -> (result, timestamp)

    def render(self, **kwargs) -> str:
        """
        渲染模板。

        Args:
            **kwargs: 变量名=值的映射

        Returns:
            渲染后的字符串
        """
        # 生成缓存 key
        cache_key = self._make_cache_key(kwargs)

        # 检查缓存
        if self._cache_ttl > 0 and cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return result

        # 编译（如需要）
        if self._compiled is None:
            self._compiled = self._parse(self.template)

        # 渲染
        result = self._render_blocks(self._compiled, kwargs)

        # 缓存
        if self._cache_ttl > 0:
            self._cache[cache_key] = (result, time.time())

        return result

    def render_once(self, **kwargs) -> str:
        """渲染一次（不使用缓存）"""
        if self._compiled is None:
            self._compiled = self._parse(self.template)
        return self._render_blocks(self._compiled, kwargs)

    def _make_cache_key(self, kwargs: Dict[str, Any]) -> str:
        """生成缓存 key"""
        items = sorted(kwargs.items())
        key_str = ",".join(f"{k}={v}" for k, v in items if not k.startswith("_"))
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def _parse(self, template: str) -> List[TemplateBlock]:
        """解析模板为块列表"""
        blocks: List[TemplateBlock] = []
        i = 0
        n = len(template)

        while i < n:
            # 查找控制块
            match_if = re.search(r'\{\{#if\s+(\w+)\}\}', template, re.IGNORECASE)
            match_each = re.search(r'\{\{#each\s+(\w+)\}\}', template, re.IGNORECASE)
            match_endif = re.search(r'\{\{/if\}\}', template, re.IGNORECASE)
            match_endeach = re.search(r'\{\{/each\}\}', template, re.IGNORECASE)
            match_else = re.search(r'\{\{else\}\}', template, re.IGNORECASE)

            # 找最近的块
            candidates = []
            if match_if:
                candidates.append(("if", match_if.start()))
            if match_each:
                candidates.append(("each", match_each.start()))
            if match_endif:
                candidates.append(("endif", match_endif.start()))
            if match_endeach:
                candidates.append(("endeach", match_endeach.start()))
            if match_else:
                candidates.append(("else", match_else.start()))

            if not candidates:
                # 剩余文本
                if i < n:
                    blocks.append(TemplateBlock(kind="text", content=template[i:]))
                break

            # 取最近的（match.start() 是相对位置，需要加 i）
            candidates.sort(key=lambda x: x[1])
            nearest_type, nearest_rel_pos = candidates[0]
            nearest_pos = i + nearest_rel_pos

            # 先添加文本（如果有）
            if i < nearest_pos:
                blocks.append(TemplateBlock(kind="text", content=template[i:nearest_pos]))

            if nearest_type == "if":
                m = re.match(r'\{\{#if\s+(\w+)\}\}', template[nearest_pos:], re.IGNORECASE)
                var = m.group(1) if m else ""
                # 找配对的 {{/if}}
                end_match = re.search(r'\{\{/if\}\}', template[nearest_pos:], re.IGNORECASE)
                if end_match:
                    # end_match.start() is relative to template[nearest_pos:]
                    inner_start = nearest_pos + m.end()
                    inner_end = nearest_pos + end_match.start()
                    inner = template[inner_start:inner_end]
                    else_match = re.search(r'\{\{else\}\}', inner, re.IGNORECASE)
                    if else_match:
                        if_block = TemplateBlock(
                            kind="if",
                            variable=var,
                            body=self._parse(inner[:else_match.start()]),
                        )
                        else_block = TemplateBlock(
                            kind="else",
                            body=self._parse(inner[else_match.end():]),
                        )
                        blocks.append(if_block)
                        blocks.append(else_block)
                    else:
                        blocks.append(TemplateBlock(
                            kind="if",
                            variable=var,
                            body=self._parse(inner),
                        ))
                    i = nearest_pos + end_match.end()
                else:
                    blocks.append(TemplateBlock(kind="text", content=template[nearest_pos:]))
                    break

            elif nearest_type == "each":
                m = re.match(r'\{\{#each\s+(\w+)\}\}', template[nearest_pos:], re.IGNORECASE)
                var = m.group(1) if m else ""
                end_match = re.search(r'\{\{/each\}\}', template[nearest_pos:], re.IGNORECASE)
                if end_match:
                    inner_start = nearest_pos + m.end()
                    inner_end = nearest_pos + end_match.start()
                    inner = template[inner_start:inner_end]
                    blocks.append(TemplateBlock(
                        kind="each",
                        variable=var,
                        body=self._parse(inner),
                    ))
                    i = nearest_pos + end_match.end()
                else:
                    blocks.append(TemplateBlock(kind="text", content=template[nearest_pos:]))
                    break

            elif nearest_type == "endif":
                # 意外 {{/if}}，作为文本
                blocks.append(TemplateBlock(kind="text", content=template[nearest_pos:nearest_pos + match_endif.end()]))
                i = nearest_pos + match_endif.end()

            elif nearest_type == "endeach":
                blocks.append(TemplateBlock(kind="text", content=template[nearest_pos:nearest_pos + match_endeach.end()]))
                i = nearest_pos + match_endeach.end()

            elif nearest_type == "else":
                blocks.append(TemplateBlock(kind="text", content=template[nearest_pos:nearest_pos + match_else.end()]))
                i = nearest_pos + match_else.end()

            else:
                i = nearest_pos + 1

        return blocks

    def _render_blocks(self, blocks: List[TemplateBlock], context: Dict[str, Any]) -> str:
        """渲染块列表"""
        result_parts = []

        i = 0
        while i < len(blocks):
            block = blocks[i]

            if block.kind == "text":
                result_parts.append(self._substitute_variables(block.content, context))
                i += 1

            elif block.kind == "if":
                value = self._get_value(block.variable, context)
                i += 1  # advance past this if block first
                # Check for else block (consumed as part of this if)
                if i < len(blocks) and blocks[i].kind == "else":
                    if value:
                        result_parts.append(self._render_blocks(block.body, context))
                    else:
                        result_parts.append(self._render_blocks(blocks[i].body, context))
                    i += 1  # consume else block
                else:
                    if value:
                        result_parts.append(self._render_blocks(block.body, context))

            elif block.kind == "each":
                items = self._get_value(block.variable, context)
                if isinstance(items, (list, tuple)):
                    for item in items:
                        item_context = dict(context)
                        if isinstance(item, dict):
                            item_context.update(item)
                        elif isinstance(item, str):
                            # $it 指向当前元素
                            item_context["it"] = item
                        result_parts.append(self._render_blocks(block.body, item_context))
                i += 1

            else:
                i += 1

        return "".join(result_parts)

    def _get_value(self, name: str, context: Dict[str, Any]) -> Any:
        """获取变量值"""
        # 支持嵌套：e.g. "user.name"
        parts = name.split(".")
        value = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _substitute_variables(self, text: str, context: Dict[str, Any]) -> str:
        """替换变量占位符"""

        # ${var:default} — 带默认值
        def replace_default(m):
            var = m.group(1)
            default = m.group(2)
            value = self._get_value(var, context)
            if value is None or value == "":
                return default
            return str(value)

        text = re.sub(r'\$\{(\w+):([^}]+)\}', replace_default, text)

        # {{variable}} — 双括号变量（无$符号，用于each循环内）
        def replace_doublebrace(m):
            var = m.group(1)
            value = self._get_value(var, context)
            if value is None:
                return m.group(0)
            return str(value)

        text = re.sub(r'\{\{(\w+)\}\}', replace_doublebrace, text)

        # $variable — 命名变量
        def replace_named(m):
            var = m.group(1)
            value = self._get_value(var, context)
            if value is None:
                return m.group(0)  # 保留原样
            return str(value)

        text = re.sub(r'\$(\w+)(?!\w|\[)', replace_named, text)

        # $0, $1 — 位置变量
        def replace_positional(m):
            idx = int(m.group(1))
            key = f"_{idx}"  # _0, _1
            value = context.get(key)
            if value is None:
                return m.group(0)
            return str(value)

        text = re.sub(r'\$(\d+)(?!\w)', replace_positional, text)

        # $ARGUMENTS — 原始参数字符串
        args = context.get("ARGUMENTS", "")
        if args:
            text = text.replace("$ARGUMENTS", str(args))

        return text

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def __repr__(self) -> str:
        return f"PromptTemplate(name={self.name!r}, description={self.description!r})"


# ============================================================================
# 模板注册表
# ============================================================================

class PromptTemplateRegistry:
    """
    Prompt 模板注册表。

    类似 SkillRegistry，但是管理 Prompt 模板。
    """

    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._lock = __import__("threading").RLock()

    def register(self, template: PromptTemplate) -> None:
        """注册模板"""
        with self._lock:
            self._templates[template.name] = template

    def get(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        with self._lock:
            return self._templates.get(name)

    def has(self, name: str) -> bool:
        """检查模板是否存在"""
        with self._lock:
            return name in self._templates

    def list_all(self) -> List[PromptTemplate]:
        """列出所有模板"""
        with self._lock:
            return list(self._templates.values())

    def render(self, name: str, **kwargs) -> str:
        """快捷渲染"""
        tmpl = self.get(name)
        if not tmpl:
            raise KeyError(f"Prompt template not found: {name}")
        return tmpl.render(**kwargs)


# 全局注册表
_template_registry: Optional[PromptTemplateRegistry] = None
_registry_lock = __import__("threading").RLock()


def get_template_registry() -> PromptTemplateRegistry:
    global _template_registry
    if _template_registry is None:
        with _registry_lock:
            if _template_registry is None:
                _template_registry = PromptTemplateRegistry()
    return _template_registry


# ============================================================================
# 内置交易模板
# ============================================================================

def register_trading_templates() -> None:
    """注册内置交易模板"""
    registry = get_template_registry()

    templates = [

        # 买入信号分析
        PromptTemplate(
            name="analyze_buy_signal",
            description="分析个股是否满足买入条件",
            template="""# 买入信号分析

## 个股信息
- 股票代码：$stock_code
- 当前价格：$current_price
- 成交量：$volume
- RSI：$rsi
- MA5：$ma5
- MA10：$ma10
- 市场状态：$market_status

## 分析要求
请根据以下策略判断是否满足买入条件：

1. **均线策略**：MA5 > MA10（多头排列）
2. **RSI策略**：RSI < 35（超卖）
3. **成交量策略**：今日成交量 > 昨日成交量的1.5倍（放量上涨）
4. **趋势策略**：价格在20日均线上方

{{#if conditions}}
满足的条件：
{{#each conditions}}- {{it}}
{{/each}}
{{else}}
当前不满足任何买入条件。
{{/if}}

## 输出格式
```json
{
  "signal": "strong_buy" | "buy" | "watch" | "none",
  "confidence": 0-100,
  "reasons": ["原因1", "原因2"],
  "risk_level": "low" | "medium" | "high"
}
```""",
        ),

        # 卖出信号分析
        PromptTemplate(
            name="analyze_sell_signal",
            description="分析持仓是否满足卖出条件",
            template="""# 卖出信号分析

## 持仓信息
- 股票代码：$stock_code
- 持仓数量：$shares
- 成本价：$cost_price
- 当前价格：$current_price
- 盈亏比例：$pnl_pct
- RSI：$rsi
- MA5：$ma5
- MA10：$ma10

## 卖出条件检查
1. **止损**：盈亏 < -8%
2. **止盈**：盈亏 > +10%/+15%/+20%（分批）
3. **RSI超买**：RSI > 70
4. **均线死叉**：MA5 < MA10

{{#if conditions}}
触发的条件：
{{#each conditions}}- {{it}}
{{/each}}
{{/if}}

## 建议
{{#if action}}
**建议：{{action}}**
{{/if}}
{{#if reason}}
原因：{{reason}}
{{/if}}""",
        ),

        # 每日复盘
        PromptTemplate(
            name="daily_review",
            description="生成每日复盘报告",
            template="""# {{date}} 每日复盘

## 账户状态
- 初始资金：¥50,000
- 期末资金：¥$final_value
- 盈亏：¥$pnl ({{pnl_pct}}%)
- 交易次数：$trade_count 次

## 持仓情况
{{#if positions}}
{{#each positions}}- {{stock_code}}：{{shares}}股，成本¥{{avg_cost}}，当前¥{{current_price}}，盈亏{{pnl_pct}}%
{{/each}}
{{else}}
空仓
{{/if}}

## 今日操作记录
{{#if trades}}
{{#each trades}}- {{time}}：{{action}} {{stock_code}} {{shares}}股 @ ¥{{price}}（理由：{{reason}}）
{{/each}}
{{else}}
无操作
{{/each}}

## 市场分析
$market_analysis

## 明日计划
$tomorrow_plan

---
*本报告由蛋蛋自动生成*""",
        ),
    ]

    for tmpl in templates:
        registry.register(tmpl)


# ============================================================================
# 便捷函数
# ============================================================================

def render_template(name: str, **kwargs) -> str:
    """快捷渲染函数"""
    return get_template_registry().render(name, **kwargs)


def create_template(template: str, name: str = "", **kwargs) -> PromptTemplate:
    """创建模板的便捷函数"""
    return PromptTemplate(template, name=name, **kwargs)
