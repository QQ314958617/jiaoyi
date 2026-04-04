"""
XML - XML解析
基于 Claude Code xml.ts 设计

XML工具。
"""
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional


def parse(text: str) -> Any:
    """
    解析XML字符串
    
    Returns:
        ElementTree根元素
    """
    return ET.fromstring(text)


def parse_file(path: str) -> Any:
    """
    解析XML文件
    
    Returns:
        ElementTree根元素
    """
    return ET.parse(path).getroot()


def to_string(element: Any, pretty: bool = False) -> str:
    """
    Element转字符串
    
    Args:
        element: ElementTree元素
        pretty: 是否格式化
    """
    if pretty:
        import xml.dom.minidom
        rough = ET.tostring(element, encoding='unicode')
        return xml.dom.minidom.parseString(rough).toprettyxml(indent="  ")
    return ET.tostring(element, encoding='unicode')


def find(element: Any, path: str) -> Optional[Any]:
    """
    查找元素
    
    Args:
        element: ElementTree元素
        path: XPath表达式
    """
    return element.find(path)


def find_all(element: Any, path: str) -> list:
    """
    查找所有匹配元素
    
    Args:
        element: ElementTree元素
        path: XPath表达式
    """
    return element.findall(path)


def text(element: Any) -> str:
    """获取文本"""
    return element.text or ""


def attr(element: Any, name: str) -> Optional[str]:
    """获取属性"""
    return element.get(name)


def attrs(element: Any) -> Dict[str, str]:
    """获取所有属性"""
    return element.attrib


def children(element: Any) -> list:
    """获取子元素"""
    return list(element)


def tag(element: Any) -> str:
    """获取标签名"""
    return element.tag


def to_dict(element: Any) -> Dict:
    """
    Element转字典
    """
    result = {
        "tag": element.tag,
        "attrs": element.attrib,
        "text": element.text or ""
    }
    
    children = list(element)
    if children:
        result["children"] = [to_dict(child) for child in children]
    
    return result


def from_dict(data: Dict) -> Any:
    """
    字典转Element
    """
    tag = data.get("tag", "item")
    attrib = data.get("attrs", {})
    text = data.get("text", "")
    
    element = ET.Element(tag, attrib)
    element.text = text
    
    if "children" in data:
        for child_data in data["children"]:
            element.append(from_dict(child_data))
    
    return element


# 导出
__all__ = [
    "parse",
    "parse_file",
    "to_string",
    "find",
    "find_all",
    "text",
    "attr",
    "attrs",
    "children",
    "tag",
    "to_dict",
    "from_dict",
]
