"""
OpenClaw Prompt Templates
====================
Inspired by Claude Code's prompt system.

提示词模板系统，支持：
1. 模板变量
2. 条件渲染
3. 循环渲染
4. 片段组合
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Union

# ============================================================================
# 模板引擎
# ============================================================================

class PromptTemplate:
    """
    提示词模板
    
    支持：
    - $variable 变量
    - ${variable:default} 带默认值的变量
    - {{variable}} Mustache 风格变量
    - {{#if condition}}...{{/if}} 条件渲染
    - {{#each items}}...{{/each}} 循环渲染
    - {{> partial}} 片段引用
    
    用法：
    ```python
    template = PromptTemplate("Hello $name!")
    result = template.render(name="World")
    # → "Hello World!"
    ```
    """
    
    def __init__(self, template: str):
        self._template = template
        self._partials: Dict[str, str] = {}
    
    def partial(self, name: str, template: Union[str, 'PromptTemplate']) -> 'PromptTemplate':
        """注册片段"""
        if isinstance(template, PromptTemplate):
            self._partials[name] = template._template
        else:
            self._partials[name] = template
        return self
    
    def render(self, **variables) -> str:
        """
        渲染模板
        
        Args:
            **variables: 模板变量
        """
        result = self._template
        
        # 处理条件块 {{#if condition}}...{{/if}}
        result = self._render_if(result, variables)
        
        # 处理循环块 {{#each items}}...{{/each}}
        result = self._render_each(result, variables)
        
        # 处理片段引用 {{> partial}}
        result = self._render_partials(result)
        
        # 处理 $variable 变量
        result = self._render_dollar_vars(result, variables)
        
        # 处理 {{variable}} Mustache 变量
        result = self._render_mustache_vars(result, variables)
        
        return result
    
    def _render_if(self, text: str, variables: Dict) -> str:
        """渲染条件块"""
        pattern = r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}'
        
        def replace_if(match):
            condition_var = match.group(1)
            content = match.group(2)
            
            value = variables.get(condition_var)
            
            if value:
                return content
            else:
                return ""
        
        result = text
        max_iterations = 100  # 防止无限循环
        iteration = 0
        
        while '{{#if' in result and iteration < max_iterations:
            result = re.sub(pattern, replace_if, result, flags=re.DOTALL)
            iteration += 1
        
        return result
    
    def _render_each(self, text: str, variables: Dict) -> str:
        """渲染循环块"""
        pattern = r'\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}'
        
        def replace_each(match):
            items_var = match.group(1)
            content_template = match.group(2)
            items = variables.get(items_var, [])
            
            if not isinstance(items, (list, tuple)):
                items = [items]
            
            results = []
            item_name = 'item'  # 默认项名
            
            # 检查是否有自定义项名 {{$item}}
            if '$' in content_template:
                item_match = re.search(r'\{\{\$(\w+)\}\}', content_template)
                if item_match:
                    item_name = item_match.group(1)
                    content_template = content_template.replace(item_match.group(0), '')
            
            for i, item in enumerate(items):
                # 如果项是字典，可以用键名访问
                item_vars = variables.copy()
                item_vars[item_name] = item
                item_vars['@index'] = i
                item_vars['this'] = item  # {{this}} 引用
                
                # 如果是字典，也展开为顶层变量
                if isinstance(item, dict):
                    for k, v in item.items():
                        if k.startswith('@'):
                            continue
                        item_vars[k] = v
                
                # 渲染这一项
                item_content = content_template
                
                # 处理项内的变量
                item_content = self._render_dollar_vars(item_content, item_vars)
                item_content = self._render_mustache_vars(item_content, item_vars)
                
                results.append(item_content)
            
            return ''.join(results)
        
        result = text
        max_iterations = 100
        iteration = 0
        
        while '{{#each' in result and iteration < max_iterations:
            result = re.sub(pattern, replace_each, result, flags=re.DOTALL)
            iteration += 1
        
        return result
    
    def _render_partials(self, text: str) -> str:
        """渲染片段引用"""
        pattern = r'\{\{>\s*(\w+)\}\}'
        
        def replace_partial(match):
            name = match.group(1)
            if name in self._partials:
                return self._partials[name]
            return f"{{>{name}}}"  # 未找到，保持原样
        
        return re.sub(pattern, replace_partial, text)
    
    def _render_dollar_vars(self, text: str, variables: Dict) -> str:
        """渲染 $variable 变量"""
        pattern = r'\$(\w+)'
        
        def replace_var(match):
            name = match.group(1)
            if name in variables:
                value = variables[name]
                if value is None:
                    return ""
                return str(value)
            return match.group(0)  # 未找到，保持原样
        
        return re.sub(pattern, replace_var, text)
    
    def _render_mustache_vars(self, text: str, variables: Dict) -> str:
        """渲染 {{variable}} 变量"""
        pattern = r'\{\{(\w+)\}\}'
        
        def replace_var(match):
            name = match.group(1)
            if name in variables:
                value = variables[name]
                if value is None:
                    return ""
                return str(value)
            return match.group(0)
        
        return re.sub(pattern, replace_var, text)
    
    def __str__(self) -> str:
        return self._template

# ============================================================================
# 便捷函数
# ============================================================================

def render_template(template: str, **variables) -> str:
    """
    渲染模板的便捷函数
    
    Example:
        render_template("Hello $name!", name="World")
    """
    t = PromptTemplate(template)
    return t.render(**variables)

# ============================================================================
# 预定义模板
# ============================================================================

TRADING_SIGNAL_TEMPLATE = """
{{#if stock_code}}
股票: {{stock_code}}
{{/if}}
{{#if signal_type}}
信号类型: {{signal_type}}
{{/if}}
{{#if strategy}}
策略: {{strategy}}
{{/if}}
{{#if reason}}
理由: {{reason}}
{{/if}}
强度: {{strength}}
"""

TRADING_REVIEW_TEMPLATE = """
=== 交易复盘 {date} ===

账户状态:
- 现金: ¥{cash}
- 持仓市值: ¥{position_value}
- 总资产: ¥{total_value}

{{#each trades}}
交易 {{@index}}:
- 操作: {{action}}
- 股票: {{stock_code}}
- 数量: {{shares}}股
- 价格: ¥{{price}}
- 金额: ¥{{amount}}
{{/each}}

胜率: {{win_rate}}%
盈亏比: {{profit_ratio}}
"""

SYSTEM_PROMPT_TEMPLATE = """
你是 {assistant_name}，一个专业的{role}。

你的职责：
{{#each responsibilities}}
- {{this}}
{{/each}}

当前时间：{current_time}

{{#if additional_context}}
额外上下文：
{additional_context}
{{/if}}
"""

# ============================================================================
# 模板管理器
# ============================================================================

class TemplateManager:
    """
    模板管理器
    
    用于管理和渲染一组相关模板
    """
    
    def __init__(self):
        self._templates: Dict[str, str] = {}
        self._compiled: Dict[str, PromptTemplate] = {}
    
    def register(self, name: str, template: str) -> None:
        """注册模板"""
        self._templates[name] = template
        self._compiled[name] = PromptTemplate(template)
    
    def render(self, name: str, **variables) -> str:
        """渲染模板"""
        if name not in self._compiled:
            if name in self._templates:
                self._compiled[name] = PromptTemplate(self._templates[name])
            else:
                raise KeyError(f"Template not found: {name}")
        
        return self._compiled[name].render(**variables)
    
    def register_partial(self, name: str, partial: str) -> None:
        """注册片段到所有模板"""
        for template in self._compiled.values():
            template.partial(name, partial)
    
    def list_templates(self) -> List[str]:
        """列出所有注册的模板"""
        return list(self._templates.keys())
