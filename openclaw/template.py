"""
Template - 模板
基于 Claude Code template.ts 设计

模板工具。
"""
from typing import Any, Dict


def render(template: str, data: Dict[str, Any]) -> str:
    """
    渲染模板
    
    Args:
        template: 模板字符串，如 "Hello {{name}}!"
        data: 数据字典
        
    Returns:
        渲染后的字符串
    """
    result = template
    
    for key, value in data.items():
        placeholder = "{{" + key + "}}"
        result = result.replace(placeholder, str(value))
    
    return result


def render_with_filters(template: str, data: Dict[str, Any]) -> str:
    """
    渲染模板（支持简单过滤器）
    
    支持 {{name|upper}}、{{name|lower}}、{{name|capitalize}}
    """
    import re
    
    result = template
    
    # 处理带过滤器的占位符
    pattern = r'\{\{(\w+)(?:\|(\w+))?\}\}'
    
    def replace_fn(match):
        key = match.group(1)
        filter_ = match.group(2)
        value = data.get(key, '')
        
        if filter_ == 'upper':
            value = str(value).upper()
        elif filter_ == 'lower':
            value = str(value).lower()
        elif filter_ == 'capitalize':
            value = str(value).capitalize()
        elif filter_ == 'trim':
            value = str(value).strip()
        elif filter_ == 'default':
            value = str(value) if value else data.get('default', '')
        
        return str(value)
    
    return re.sub(pattern, replace_fn, result)


def compile_template(template: str) -> callable:
    """
    编译模板为函数
    
    Args:
        template: 模板字符串
        
    Returns:
        (data) -> str 函数
    """
    def compiled(data: Dict[str, Any]) -> str:
        return render(template, data)
    
    return compiled


class TemplateEngine:
    """
    模板引擎
    """
    
    def __init__(self):
        self._templates: Dict[str, str] = {}
    
    def add(self, name: str, template: str) -> None:
        """添加模板"""
        self._templates[name] = template
    
    def get(self, name: str) -> str:
        """获取模板"""
        return self._templates.get(name)
    
    def render(self, name: str, data: Dict[str, Any]) -> str:
        """渲染模板"""
        template = self._templates.get(name)
        if template is None:
            raise KeyError(f"Template not found: {name}")
        return render_with_filters(template, data)


# 导出
__all__ = [
    "render",
    "render_with_filters",
    "compile_template",
    "TemplateEngine",
]
