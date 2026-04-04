"""
Template2 - 模板2
基于 Claude Code template2.ts 设计

更多模板工具。
"""
from typing import Any, Callable, Dict, List


def interpolate(template: str, data: dict) -> str:
    """
    模板插值
    
    Args:
        template: 模板字符串 (如 "Hello {name}")
        data: 数据字典
        
    Returns:
        插值后的字符串
    """
    result = template
    
    for key, value in data.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value))
    
    return result


def template(template_str: str) -> Callable[[dict], str]:
    """
    创建模板函数
    
    Args:
        template_str: 模板字符串
        
    Returns:
        (data) -> str
    """
    def apply(data: dict) -> str:
        return interpolate(template_str, data)
    
    return apply


class Template:
    """
    模板类
    
    支持条件、循环等。
    """
    
    def __init__(self, template_str: str):
        """
        Args:
            template_str: 模板字符串
        """
        self._template = template_str
    
    def render(self, data: dict) -> str:
        """渲染模板"""
        result = self._template
        
        # 简单条件 {{if condition}}...{{endif}}
        import re
        
        # if blocks
        pattern = r'\{\{if\s+(\w+)\}\}(.*?)\{\{endif\}\}'
        
        def replace_if(match):
            var_name = match.group(1)
            content = match.group(2)
            
            if var_name in data and data[var_name]:
                return content
            return ''
        
        result = re.sub(pattern, replace_if, result, flags=re.DOTALL)
        
        # for loops {{for item in items}}...{{endfor}}
        pattern = r'\{\{for\s+(\w+)\s+in\s+(\w+)\}\}(.*?)\{\{endfor\}\}'
        
        def replace_for(match):
            item_name = match.group(1)
            list_name = match.group(2)
            content = match.group(3)
            
            if list_name not in data:
                return ''
            
            items = data[list_name]
            if not isinstance(items, list):
                return ''
            
            results = []
            for item in items:
                item_data = {item_name: item}
                # 展平字典
                if isinstance(item, dict):
                    item_data.update(item)
                results.append(interpolate(content, item_data))
            
            return ''.join(results)
        
        result = re.sub(pattern, replace_for, result, flags=re.DOTALL)
        
        # 变量 {{var}}
        result = interpolate(result, data)
        
        return result


def create_template(template_str: str) -> Template:
    """
    创建模板
    
    Args:
        template_str: 模板字符串
        
    Returns:
        Template实例
    """
    return Template(template_str)


class TemplateEngine:
    """
    模板引擎
    
    管理多个模板。
    """
    
    def __init__(self):
        self._templates: Dict[str, Template] = {}
    
    def add(self, name: str, template_str: str) -> None:
        """添加模板"""
        self._templates[name] = Template(template_str)
    
    def render(self, name: str, data: dict) -> str:
        """渲染模板"""
        if name not in self._templates:
            raise KeyError(f"Template not found: {name}")
        return self._templates[name].render(data)
    
    def has(self, name: str) -> bool:
        """检查模板是否存在"""
        return name in self._templates


# 导出
__all__ = [
    "interpolate",
    "template",
    "Template",
    "create_template",
    "TemplateEngine",
]
