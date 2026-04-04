"""
EnvConfig - 环境配置
基于 Claude Code envConfig.ts 设计

环境变量配置工具。
"""
import os
from typing import Any, Dict, List, Optional


class EnvConfig:
    """
    环境配置
    
    从环境变量读取配置。
    """
    
    def __init__(self, prefix: str = '', separator: str = '_'):
        """
        Args:
            prefix: 环境变量前缀
            separator: 分隔符（用于嵌套键）
        """
        self._prefix = prefix
        self._separator = separator
        self._cache: Dict[str, Any] = {}
    
    def get(self, key: str, default: Any = None, type: type = None) -> Any:
        """
        获取配置
        
        Args:
            key: 键（支持点分隔）
            default: 默认值
            type: 类型（int, float, bool, str）
            
        Returns:
            配置值
        """
        env_key = self._to_env_key(key)
        
        if env_key in self._cache:
            return self._cache[env_key]
        
        value = os.environ.get(env_key, None)
        
        if value is None:
            return default
        
        # 类型转换
        if type:
            value = self._convert(value, type)
        
        self._cache[env_key] = value
        return value
    
    def _to_env_key(self, key: str) -> str:
        """转换为环境变量键"""
        if self._prefix:
            key = f"{self._prefix}{self._separator}{key}"
        return key.upper().replace('.', self._separator.upper())
    
    def _convert(self, value: str, type: type) -> Any:
        """类型转换"""
        if type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        if type == int:
            return int(value)
        if type == float:
            return float(value)
        return value
    
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数"""
        return self.get(key, default, int)
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数"""
        return self.get(key, default, float)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔值"""
        return self.get(key, default, bool)
    
    def get_str(self, key: str, default: str = '') -> str:
        """获取字符串"""
        return self.get(key, default, str)
    
    def get_list(self, key: str, separator: str = ',', default: List = None) -> List:
        """获取列表"""
        value = self.get(key)
        if value is None:
            return default or []
        return [v.strip() for v in value.split(separator)]
    
    def required(self, key: str, type: type = None) -> Any:
        """
        获取必需的配置
        
        Raises:
            KeyError: 配置不存在
        """
        value = self.get(key, type=type)
        if value is None:
            raise KeyError(f"Required environment variable not set: {self._to_env_key(key)}")
        return value
    
    def is_set(self, key: str) -> bool:
        """检查配置是否设置"""
        env_key = self._to_env_key(key)
        return env_key in os.environ
    
    def names(self) -> List[str]:
        """获取所有环境变量名（带前缀）"""
        prefix = f"{self._prefix}{self._separator}" if self._prefix else ''
        prefix_upper = prefix.upper()
        
        return [
            k for k in os.environ.keys()
            if k.startswith(prefix_upper)
        ]
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    def reload(self) -> None:
        """重新加载"""
        self.clear_cache()


# 全局实例
_global_env_config: Optional[EnvConfig] = None


def env_config(prefix: str = '', separator: str = '_') -> EnvConfig:
    """
    获取环境配置
    
    Args:
        prefix: 前缀
        separator: 分隔符
        
    Returns:
        EnvConfig实例
    """
    global _global_env_config
    
    if _global_env_config is None:
        _global_env_config = EnvConfig(prefix, separator)
    
    return _global_env_config


# 导出
__all__ = [
    "EnvConfig",
    "env_config",
]
