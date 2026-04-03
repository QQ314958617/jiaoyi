"""
OpenClaw Unified Tool Registry
================================
Inspired by Claude Code's tools.ts and Tool.ts architecture.

设计目标：
- 统一管理所有工具的注册、发现、生命周期
- 支持工具的 is_enabled() 开关（feature flag 集成）
- 支持按类别分组过滤
- 统一的 API 路由生成

架构：
    registry.py          ← 全局工具注册表
    tools/
        base.py          ← 工具基类（类似 buildTool）
        trade.py          ← 交易工具
        market.py         ← 市场数据工具
        review.py         ← 复盘工具
        ...

使用方式：

    from openclaw.tools.registry import tool_registry, tool

    @tool_registry.register
    class PortfolioTool(BaseTool):
        name = "portfolio"
        description = "获取账户和持仓"
        category = "trading"
        is_enabled = lambda: feature("TRADING_AUTO_MODE")

    # Flask 路由自动生成
    @tool_registry.api_route("/api/portfolio", methods=["GET"])
    def get_portfolio():
        return tool_registry.get("portfolio").execute()
"""

import importlib
import pkgutil
from   pathlib import Path
from   typing import Any, Callable, Dict, List, Optional, Set, Type
from   dataclasses import dataclass, field, field
from   abc import ABC, abstractmethod
import threading

from openclaw.feature_flags import is_feature_enabled


# ============================================================================
# 工具基类（对应 Claude Code 的 Tool.ts buildTool）
# ============================================================================

@dataclass
class ToolMetadata:
    """工具元信息"""
    name: str
    description: str
    category: str = "general"          # trading/market/system/general
    tags: Set[str] = field(default_factory=set)
    version: str = "1.0.0"
    author: str = ""
    is_critical: bool = False          # 关键工具，禁用时整个系统告警


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    cached: bool = False               # 是否来自缓存

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "cached": self.cached,
        }


class BaseTool(ABC):
    """
    工具基类。

    子类必须定义：
        name: str           - 工具唯一名称
        description: str     - 工具描述

    可选覆盖：
        category: str       - 分类（默认 "general"）
        tags: Set[str]      - 标签
        is_enabled(): bool  - 是否启用
        execute(): ToolResult - 执行逻辑
    """

    # 类属性（子类必须定义）
    name: str = ""
    description: str = ""

    # 可选类属性
    category: str = "general"
    tags: Set[str] = field(default_factory=set)
    version: str = "1.0.0"

    # Feature flag 名（如果工具依赖特性开关）
    feature_flag: Optional[str] = None

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name=self.name,
            description=self.description,
            category=self.category,
            tags=self.tags,
            version=self.version,
        )

    def is_enabled(self) -> bool:
        """工具是否启用（可被子类override）"""
        if self.feature_flag:
            return is_feature_enabled(self.feature_flag)
        return True

    def execute(self, *args, **kwargs) -> ToolResult:
        """执行工具，子类必须实现"""
        raise NotImplementedError(f"Tool {self.name} must implement execute()")

    def validate_input(self, *args, **kwargs) -> Optional[str]:
        """验证输入参数，返回错误信息或None"""
        return None


# ============================================================================
# Flask 路由装饰器支持
# ============================================================================

@dataclass
class ApiRoute:
    """API路由定义"""
    path: str
    methods: List[str]
    tool_name: str
    handler: Optional[Callable] = None


# ============================================================================
# 工具注册表（对应 Claude Code 的 tools.ts getAllBaseTools）
# ============================================================================

class ToolRegistry:
    """
    全局工具注册表。

    用法:
        registry = ToolRegistry()

        @registry.register
        class MyTool(BaseTool):
            name = "my_tool"
            ...

        # 获取工具
        tool = registry.get("my_tool")

        # 列出所有启用的工具
        enabled = registry.list_enabled()

        # 按分类获取
        trading_tools = registry.list_by_category("trading")
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._lock = threading.RLock()
        self._api_routes: List[ApiRoute] = []
        self._initialized = False

    def register(self, tool_cls: Optional[Type[BaseTool]] = None, *, name: Optional[str] = None) -> Type[BaseTool]:
        """
        装饰器用法：
            @registry.register
            class MyTool(BaseTool):
                ...

        直接调用用法：
            registry.register(MyTool)
        """
        def decorator(cls: Type[BaseTool]) -> Type[BaseTool]:
            instance = cls()
            tool_name = name or instance.name
            if not tool_name:
                raise ValueError(f"Tool class {cls.__name__} has no name")

            with self._lock:
                self._tools[tool_name] = instance

            # 导出类以便后续访问
            setattr(cls, "_registry", self)
            setattr(cls, "_tool_name", tool_name)
            return cls

        if tool_cls is None:
            # 装饰器带参数：@registry.register(name="xxx")
            return decorator
        else:
            return decorator(tool_cls)

    def get(self, name: str) -> Optional[BaseTool]:
        """获取工具实例"""
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> BaseTool:
        """获取工具，不存在则抛异常"""
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Tool '{name}' not found in registry")
        return tool

    def list_all(self) -> List[BaseTool]:
        """列出所有已注册的工具"""
        return list(self._tools.values())

    def list_enabled(self) -> List[BaseTool]:
        """列出所有已启用且 feature flag 开启的工具"""
        return [t for t in self._tools.values() if t.is_enabled()]

    def list_by_category(self, category: str) -> List[BaseTool]:
        """按分类列出工具"""
        return [t for t in self._tools.values()
                if t.category == category and t.is_enabled()]

    def list_names(self, enabled_only: bool = False) -> List[str]:
        """列出所有工具名称"""
        tools = self.list_enabled() if enabled_only else self.list_all()
        return [t.name for t in tools]

    def api_route(self, path: str, methods: Optional[List[str]] = None):
        """
        Flask 路由装饰器，自动绑定到工具。

        用法:
            @registry.api_route("/api/portfolio", methods=["GET"])
            def get_portfolio():
                return registry.get("portfolio").execute()
        """
        if methods is None:
            methods = ["GET"]

        def decorator(func: Callable) -> Callable:
            route = ApiRoute(
                path=path,
                methods=methods,
                tool_name=func.__name__,
                handler=func,
            )
            self._api_routes.append(route)
            return func
        return decorator

    @property
    def routes(self) -> List[ApiRoute]:
        """获取所有已注册的 API 路由"""
        return self._api_routes

    def auto_discover(self, package_path: str = "openclaw.tools") -> int:
        """
        自动发现并注册 package_path 下的所有工具。

        遍历模块目录，将所有 BaseTool 子类自动注册。
        返回注册数量。
        """
        count = 0
        try:
            package = importlib.import_module(package_path)
            package_dir = Path(package.__file__).parent

            for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
                if module_name in ("registry", "base", "__"):
                    continue
                try:
                    module = importlib.import_module(f"{package_path}.{module_name}")
                    # 注册模块中所有 BaseTool 子类
                    for attr_name in dir(module):
                        cls = getattr(module, attr_name, None)
                        if (isinstance(cls, type) and
                            issubclass(cls, BaseTool) and
                            cls is not BaseTool and
                            hasattr(cls, "name") and
                            cls.name):  # 只注册有 name 的
                            self.register(cls)
                            count += 1
                except Exception:
                    pass
        except Exception:
            pass
        return count

    def stats(self) -> Dict[str, Any]:
        """注册表统计"""
        all_tools = self.list_all()
        enabled = self.list_enabled()
        categories = {}
        for t in all_tools:
            categories.setdefault(t.category, []).append(t.name)

        return {
            "total_registered": len(all_tools),
            "total_enabled": len(enabled),
            "disabled": len(all_tools) - len(enabled),
            "categories": {k: len(v) for k, v in categories.items()},
            "routes": len(self._api_routes),
        }


# ============================================================================
# 全局单例
# ============================================================================

tool_registry = ToolRegistry()


# ============================================================================
# 便捷装饰器（全局注册表）
# ============================================================================

def register_tool(cls: Optional[Type[BaseTool]] = None, *, name: Optional[str] = None) -> Type[BaseTool]:
    """
    全局注册装饰器。
    用法：
        @register_tool
        class MyTool(BaseTool):
            name = "my_tool"
            ...
    """
    return tool_registry.register(cls, name=name)


# ============================================================================
# 预置基础工具类别
# ============================================================================

TOOL_CATEGORIES = {
    "trading": "交易相关工具（下单/查询持仓）",
    "market": "市场数据工具（行情/指数）",
    "review": "复盘工具（每日复盘/统计）",
    "system": "系统工具（状态/配置）",
    "general": "通用工具",
}
