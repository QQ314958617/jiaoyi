# Claude Code 源码学习进度

## 学习顺序（按计划v2）
优先级从高到低，依次学习：

| # | 模块 | 源码文件 | 状态 |
|---|------|---------|------|
| 1 | Feature Flag系统 | `src/utils/featureFlags.ts` | ✅ 已完成 |
| 2 | 上下文缓存 | `src/context.ts` | ✅ 已完成 |
| 3 | BaseTool工具体系 | `src/Tool.ts` | ✅ 已完成 |
| 4 | 工具注册表 | `src/tools.ts` | ✅ 已完成 |
| 5 | Agent上下文隔离 | `src/utils/agentContext.ts` | ✅ 已完成 |
| 6 | AgentTool嵌套 | `src/tools/AgentTool/AgentTool.tsx` | ✅ 已完成 |
| 7 | Bash权限分类器 | `src/tools/BashTool/bashPermissions.ts` | ✅ 已完成 |
| 8 | Hooks系统 | `src/utils/hooks.ts` | ✅ 已完成 |
| 9 | SkillTool | `src/tools/SkillTool/SkillTool.ts` | ✅ 已完成 |
| 10 | MCP系统 | `src/services/mcp/client.ts` | ✅ 已完成 |
| 11 | 命令注册表 | `src/commands.ts` | ✅ 已完成（SkillRegistry已覆盖）|
| 12 | 状态管理 | `src/state/AppState.tsx` | ✅ 已完成 |

## 当前进度
- 当前模块：第4轮学习进行中
- 第1轮：1-12全部完成
- 第2轮（17:04-18:05）：8项全部完成
- 第3轮（18:05起）：系统集成+实用化
  - ✅ 历史记录系统（trading_history.py）
  - ✅ 盘中监控API链打通
  - ✅ 5个交易cron状态推送
- 第4轮（21:06起）：实用化模块
  - ✅ cost-tracker.ts → cost_tracker.py（成本追踪系统）
  - ✅ stream.ts → Stream类（async流式迭代器）

## 新增模块
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 13 | 历史记录系统 | `src/history.ts` | trading_history.py | ✅ |
| 14 | 成本追踪 | `src/cost-tracker.ts` | cost_tracker.py | ✅ |
| 15 | Async Stream | `src/utils/stream.ts` | agent_tool.py Stream类 | ✅ |
| 16 | Prompt模板 | `src/utils/argumentSubstitution.ts` | prompt_template.py | ✅ |
| 17 | 重试+限流 | `rateLimitMessages.ts` | retry.py | ✅ |
| 18 | TTL缓存 | `src/utils/memoize.ts` | memoize.py | ✅ |
| 19 | 上下文分析 | `src/utils/contextAnalysis.ts` | context_analyzer.py | ✅ |
| 20 | HTTP预热 | `src/utils/apiPreconnect.ts` | preconnect.py | ✅ |
| 21 | 优雅退出 | `cleanupRegistry.ts` | cleanup.py | ✅ |
| 22 | 数据Diff | `diff.ts` | diff.py | ✅ |
| 23 | 文件监控 | `fileChangedWatcher.ts` | file_watcher.py | ✅ |
| 24 | 结构化日志 | `internalLogging.ts` | logger.py | ✅ |
| 25 | MCP客户端 | `src/services/mcp/client.ts` | mcp_client.py | ✅ |
| 26 | 异步Stream | `src/utils/stream.ts` | stream.py | ✅ |
| 27 | 代理客户端 | `upstreamproxy.ts` | proxy.py | ✅ |
| 28 | 事件分析 | `src/services/analytics/index.ts` | analytics.py | ✅ |
| 29 | 错误处理 | `src/utils/errors.ts` | errors.py | ✅ |
| 30 | 事件信号 | `src/utils/signal.ts` | signal.py | ✅ |
| 31 | 任务队列 | `src/utils/sdkEventQueue.ts` | task_queue.py | ✅ |
| 32 | 缓存系统 | `src/utils/fileReadCache.ts` | cache.py | ✅ |
| 33 | 文件锁 | `src/utils/lockfile.ts` | lockfile.py | ✅ |
| 34 | 环境工具 | `src/utils/env.ts` | env.py | ✅ |
| 35 | ID生成器 | `src/utils/uuid.ts` | id.py | ✅ |
| 36 | 格式化工具 | `src/utils/format.ts` | format.py | ✅ |
| 37 | 文本截断 | `src/utils/truncate.ts` | truncate.py | ✅ |
| 38 | JSON处理 | `src/utils/json.ts` | json_utils.py | ✅ |

## 更新规则
每次学习完一个模块，在此文件更新"当前模块"为下一个
