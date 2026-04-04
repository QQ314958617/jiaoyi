"""
Template - 模板引擎
基于 Claude Code template.ts 设计

简单的字符串模板替换。
"""
import re
from typing import Any, Dict, Optional


class Template:
    """
    字符串模板
    
    支持{{variable}}和{{#if}}等语法。
    """
    
    def __init__(self, template: str):
        """
        Args:
            template: 模板字符串
        """
        self._template = template
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        渲染模板
        
        Args:
            context: 变量上下文
            
        Returns:
            渲染后的字符串
        """
        result = self._template
        
        # 简单变量替换
        for key, value in context.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        
        return result
    
    def render_conditional(
        self,
        context: Dict[str, Any],
        if_pattern: str = r"{{#if\s+(\w+)}}([\s\S]*?){{/if}}",
        endif_pattern: str = r"{{/if}}",
    ) -> str:
        """
        渲染条件模板
        
        Args:
            context: 变量上下文
            if_pattern: if正则
            endif_pattern: endif正则
            
        Returns:
            渲染后的字符串
        """
        result = self._template
        
        # 查找所有if块
        if_blocks = re.finditer(if_pattern, result)
        
        for match in if_blocks:
            var_name = match.group(1)
            content = match.group(2)
            
            if var_name in context and context[var_name]:
                # 条件为真，保留内容
                result = result.replace(match.group(0), content)
            else:
                # 条件为假，移除内容
                result = result.replace(match.group(0), "")
        
        return result


def render(template: str, context: Dict[str, Any]) -> str:
    """
    渲染模板字符串
    
    Args:
        template: 模板字符串
        context: 变量上下文
        
    Returns:
        渲染后的字符串
    """
    t = Template(template)
    return t.render(context)


def render_with_conditionals(
    template: str,
    context: Dict[str, Any],
) -> str:
    """
    渲染带条件的模板
    
    Args:
        template: 模板字符串
        context: 变量上下文
        
    Returns:
        渲染后的字符串
    """
    t = Template(template)
    result = t.render_conditional(context)
    return t.render(context)


def interpolate(
    template: str,
    **kwargs: Any,
) -> str:
    """
    插值渲染
    
    Args:
        template: 模板字符串
        **kwargs: 变量
        
    Returns:
        渲染后的字符串
    """
    return render(template, kwargs)


# 导出
__all__ = [
    "Template",
    "render",
    "render_with_conditionals",
    "interpolate",
]
