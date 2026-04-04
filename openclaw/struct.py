"""
Struct - 结构体
基于 Claude Code struct.ts 设计

结构化数据类型。
"""
from typing import Any, Dict, TypeVar


T = TypeVar('T')


class Struct:
    """
    结构体
    
    类似于TypeScript的interface。
    """
    
    def __init__(self, data: Dict[str, Any] = None):
        """
        Args:
            data: 初始数据
        """
        if data:
            for key, value in data.items():
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def __repr__(self) -> str:
        return f"Struct({self.to_dict()})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Struct):
            return False
        return self.to_dict() == other.to_dict()
    
    def __getitem__(self, key: str) -> Any:
        """字典式访问"""
        return getattr(self, key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """字典式设置"""
        setattr(self, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取属性（带默认值）"""
        return getattr(self, key, default)


def create_struct(schema: Dict[str, type]) -> type:
    """
    创建结构体类型
    
    Args:
        schema: 字段定义 {字段名: 类型}
        
    Returns:
        结构体类
    """
    class TypedStruct(Struct):
        pass
    
    for field, field_type in schema.items():
        setattr(TypedStruct, field, None)
    
    return TypedStruct


def struct_to_dict(struct: Struct) -> Dict[str, Any]:
    """结构体转字典"""
    return struct.to_dict()


def dict_to_struct(data: Dict[str, Any], struct_type: type = None) -> Struct:
    """
    字典转结构体
    
    Args:
        data: 字典数据
        struct_type: 结构体类型（可选）
        
    Returns:
        结构体实例
    """
    if struct_type:
        return struct_type(data)
    return Struct(data)


def pick_struct_fields(data: Dict[str, Any], fields: list) -> Dict[str, Any]:
    """
    选取结构体字段
    
    Args:
        data: 数据字典
        fields: 要选取的字段列表
        
    Returns:
        筛选后的字典
    """
    return {k: v for k, v in data.items() if k in fields}


def omit_struct_fields(data: Dict[str, Any], fields: list) -> Dict[str, Any]:
    """
    排除结构体字段
    
    Args:
        data: 数据字典
        fields: 要排除的字段列表
        
    Returns:
        筛选后的字典
    """
    return {k: v for k, v in data.items() if k not in fields}


def merge_structs(*structs: Struct) -> Struct:
    """
    合并结构体
    
    Args:
        *structs: 结构体列表
        
    Returns:
        合并后的结构体
    """
    result = {}
    
    for struct in structs:
        if isinstance(struct, Struct):
            result.update(struct.to_dict())
    
    return Struct(result)


# 导出
__all__ = [
    "Struct",
    "create_struct",
    "struct_to_dict",
    "dict_to_struct",
    "pick_struct_fields",
    "omit_struct_fields",
    "merge_structs",
]
