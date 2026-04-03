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
- 当前模块：第2轮深化中
- 已完成第1轮：1,2,3,4,5,6,7,8,9,10,11,12
- 第2轮已完成（17:04-17:22）：
  - ✅ skill_system + mcp_client 深度集成
  - ✅ SkillExecutorV2 (MiniMax API调用)
  - ✅ state_manager + Star Office AI工作室状态同步
  - ✅ /api/agent_status HTTP接口（GET/POST）
  - ✅ 盘中监控cron状态推送（researching/executing/idle）
- 第2轮待完成：
  - ⬜ agent_tool execute_agent() 接真实AI模型
  - ⬜ bashPermissions pathValidation/sedValidation深化
  - ⬜ AgentTool流式输出

## 更新规则
每次学习完一个模块，在此文件更新"当前模块"为下一个
