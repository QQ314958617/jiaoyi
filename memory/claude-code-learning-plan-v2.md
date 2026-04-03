# Claude Code 源码深度学习与 OpenClaw 运用方案
**总代码量**：1,899 文件 | 1,026,630 行 | TypeScript + Bun + React/Ink

---

## 📊 模块全景图

| 模块 | 文件数 | 行数 | 核心文件 | 对 OpenClaw 价值 |
|------|--------|------|----------|-----------------|
| **工具系统** | 45+ | ~80,000 | `tools.ts`, `Tool.ts`, `AgentTool.tsx` | ⭐⭐⭐⭐⭐ |
| **权限安全** | 25+ | ~40,000 | `bashPermissions.ts`, `permissions.ts` | ⭐⭐⭐⭐⭐ |
| **Agent 系统** | 20+ | ~50,000 | `AgentTool.tsx`, `runAgent.ts`, `agentContext.ts` | ⭐⭐⭐⭐⭐ |
| **上下文系统** | 15+ | ~15,000 | `context.ts`, `claudemd.ts`, `memdir.ts` | ⭐⭐⭐⭐⭐ |
| **Hooks 系统** | 20+ | ~5,000 | `hooks.ts`, `registerSkillHooks.ts` | ⭐⭐⭐⭐ |
| **状态管理** | 30+ | ~30,000 | `AppState.tsx`, `AppStateStore.ts` | ⭐⭐⭐⭐ |
| **查询引擎** | 10+ | ~20,000 | `query.ts`, `queryContext.ts` | ⭐⭐⭐⭐ |
| **MCP 系统** | 25+ | ~30,000 | `services/mcp/*.ts` | ⭐⭐⭐⭐ |
| **命令系统** | 70+ | ~50,000 | `commands.ts`, `commands/*/` | ⭐⭐⭐ |
| **UI/TUI** | 300+ | ~200,000 | `components/`, `ink/` | ⭐⭐ |
| **插件系统** | 40+ | ~40,000 | `services/plugins/*.ts` | ⭐⭐⭐ |
| **Analytics** | 20+ | ~15,000 | `services/analytics/`, `growthbook.ts` | ⭐⭐ |

---

## 🎯 模块一：工具系统（最高优先级）
**文件**：`src/tools.ts`（3500行）| `src/Tool.ts`（1000行）| 各工具子目录

### 架构拆解

```
tools.ts ──── 工具注册表（getAllBaseTools / getToolsForDefaultPreset）
    │
    ├── Tool.ts ──────── buildTool() 工厂函数（工具定义标准）
    │                    - inputSchema / outputSchema
    │                    - prompt() 生成 AI 提示词
    │                    - result() 渲染输出 UI
    │                    - describe() CLI 描述
    │
    ├── AgentTool/ ───── 233KB，嵌套 Agent 核心
    │   ├── runAgent.ts  ── 子 Agent 执行循环
    │   ├── forkSubagent.ts ── 子 Agent fork 机制
    │   └── UI.tsx       ── Agent 结果渲染
    │
    ├── BashTool/ ────── 160KB，Shell 执行
    │   ├── bashPermissions.ts ── 2621行！命令权限分类器
    │   ├── bashSecurity.ts ── 危险命令检测
    │   ├── readOnlyValidation.ts ── 只读模式验证
    │   └── pathValidation.ts ── 路径约束
    │
    ├── SkillTool/ ───── 38KB，Skill 执行器
    ├── WebSearchTool/ ── 网络搜索
    ├── WebFetchTool/ ─── 网页获取
    ├── FileEditTool/ ─── 文件编辑
    ├── ScheduleCronTool/ ─ 定时任务（Create/List/Delete）
    ├── TaskCreateTool/ / TaskListTool/ / TaskGetTool/ ── 任务管理
    ├── MCPTool/ ──────── MCP 工具包装
    ├── GlobTool/ / GrepTool/ ── 文件搜索
    └── ... 共 43 个工具
```

### 关键设计模式

#### 1. buildTool 工厂函数（Tool.ts）
```typescript
// 每个工具都是这样定义的
const MyTool = buildTool({
  name: 'my-tool',
  description: 'What this tool does',
  inputSchema: z.object({ ... }),
  outputSchema: z.object({ ... }),
  async prompt({ input, tools, ... }) { ... },    // 生成 AI 提示词
  async result({ output, ... }) { ... },           // 渲染结果 UI
  describe({ params }) { return '...'},             // CLI 描述
  // 可选
  about: 'Longer description for help',
  matches: ['task-creation'],  // 工具分类标签
})
```

#### 2. 工具注册表（tools.ts）
```typescript
// 按预设分组获取工具
getToolsForDefaultPreset(preset: 'read'|'edit'|'agent'|'minimal')
// 动态条件注册
if (feature('AGENT_TRIGGERS')) {
  cronTools = [CronCreateTool, ...]
}
// 工具池：assembleToolPool() = 扁平化所有工具
```

#### 3. Bash 权限分类器（bashPermissions.ts，2621行）
```
命令输入
    ↓
splitCommand() 分割子命令
    ↓
parseForSecurityFromAst() AST 分析
    ↓
classifyBashCommand() 分类器判断
    ↓
PermissionResult { allow / deny / ask }
    ↓
用户交互或自动决策
```
**关键机制**：
- `checkSemantics()` — 语义分析（不只是字符串匹配）
- `bashClassifier` — AI 辅助判断危险命令
- 规则匹配：`permissionRuleExtractPrefix` + `matchWildcardPattern`
- 沙箱模式：`shouldUseSandbox()` → `SandboxManager`

### OpenClaw 运用方案

| 目标 | 具体任务 | 文件 |
|------|---------|------|
| 改造工具注册 | 把 app.py 的 Flask 路由改造为 `BaseTool` 子类 | `openclaw/tools/trade.py` |
| 注册表发现 | 完成 `auto_discover()` 集成 | `openclaw/tools/__init__.py` |
| 权限模型 | 引入 `bashPermissions` 的规则匹配逻辑到 exec 工具 | `openclaw/tools/security.py` |
| Skill 工具 | 借鉴 `SkillTool` 重构 skill 加载机制 | `openclaw/tools/skill_tool.py` |
| 任务系统 | 参考 `TaskCreateTool` 实现 todo 待办 | `openclaw/tools/todo.py` |

---

## 🎯 模块二：权限与安全系统（最高优先级）
**文件**：`src/utils/permissions/` | `src/tools/BashTool/bashPermissions.ts`

### 架构拆解

```
permissions/
├── permissions.ts ──────── 核心：checkPermissions() / createPermissionRequestMessage()
├── PermissionRule.ts ───── 规则定义（toolName + ruleContent + behavior）
├── PermissionMode.ts ────── 权限模式（default/ask/allow/deny）
├── PermissionResult.ts ──── 决策结果（reason + behavior）
├── bashClassifier.ts ───── Bash 命令 AI 分类器
├── shellRuleMatching.ts ─── 通配符规则匹配
├── autoModeState.ts ─────── 自动模式状态机
├── PermissionUpdate.ts ──── 规则更新（添加/删除/修改）
├── bypassPermissionsKillswitch.ts ── 权限绕过开关
└── dangerousPatterns.ts ─── 危险命令模式库
```

### 核心流程

```typescript
// 1. 权限检查入口
async function checkPermissions(
  tool: BaseTool,
  input: unknown,
  context: ToolPermissionContext
): Promise<PermissionResult>

// 2. 三种权限模式
enum PermissionMode {
  default = 'default',   // 按规则走
  ask = 'ask',           // 总是询问
  allow = 'allow',       // 总是允许
  deny = 'deny'          // 总是拒绝
}

// 3. 权限规则结构
interface PermissionRule {
  toolName: string
  ruleContent?: string   // 如 "git commit --amend"，支持通配符
  behavior: 'allow' | 'deny' | 'ask'
  source: 'user' | 'plugin' | 'managed'  // 规则来源
}

// 4. 规则匹配（shellRuleMatching.ts）
matchWildcardPattern(pattern: string, command: string): boolean
permissionRuleExtractPrefix(rule: string): string  // 提取前缀优化匹配
```

### Bash 权限分类器详细流程

```
bashPermissions.ts 核心逻辑（2621行）：

checkBashToolPermission(input)
    │
    ├── splitCommand() ─── 解析成子命令数组
    │   └── 防止 ReDoS 攻击（MAX_SUBCOMMANDS=50）
    │
    ├── for each subcommand:
    │   ├── parseForSecurityFromAst() ─── tree-sitter AST
    │   │   ├── extractOutputRedirections() ─ 提取重定向
    │   │   ├── getCommandSubcommandPrefix() ── 提取子命令前缀
    │   │   └── checkCommandOperatorPermissions() ── && || ; 等
    │   │
    │   ├── classifyBashCommand() ──── 分类器
    │   │   ├── isEnvVarAssignment() ── 环境变量赋值（安全）
    │   │   ├── checkBuiltInSafety() ── 内建命令白名单
    │   │   ├── checkPathConstraints() ── 路径约束（--path 参数）
    │   │   └── isDangerousPattern() ── 危险模式匹配
    │   │
    │   └── 根据结果
    │       ├── allow → 直接执行
    │       ├── deny → 拦截并说明原因
    │       └── ask → 弹出权限对话框
    │
    └── 沙箱降级
        └── if (shouldUseSandbox()) → SandboxManager.run()
```

### OpenClaw 运用方案

| 目标 | 具体任务 | 文件 |
|------|---------|------|
| exec 权限规则 | 引入 PermissionRule 系统，管控危险命令 | `openclaw/tools/security.py` |
| 规则持久化 | 规则存入 `~/.openclaw/rules.json` | `openclaw/rules.py` |
| 权限模式 | 实现 `PermissionMode`（openclaw exec 可配置） | `openclaw/config.py` |
| 危险命令库 | 参考 `dangerousPatterns.ts` 建立 OpenClaw 危险命令库 | `openclaw/tools/security.py` |
| 路径约束 | 参考 `pathValidation.ts`，限制 exec 可访问的目录 | `openclaw/tools/security.py` |

---

## 🎯 模块三：Agent 系统（最高优先级）
**文件**：`src/tools/AgentTool/`（233KB）| `src/utils/agentContext.ts`（178行）

### 架构拆解

```
AgentTool.tsx ──────── 1397行，工具入口
  ├── 输入 schema：
  │   {
  │     description,    // 任务描述
  │     prompt,         // 任务指令
  │     subagent_type,  // agent类型（built-in/custom）
  │     model,          // 模型选择
  │     run_in_background,
  │     name,           // 队友名称
  │     team_name,      // 团队名
  │     mode,           // 权限模式
  │     isolation       // worktree | remote
  │   }
  │
  ├── runAgent() ────── 子Agent执行循环（最核心）
  │   ├── 初始化 MCP 连接
  │   ├── 构建系统提示词
  │   ├── assembleToolPool() ── 获取可用工具池
  │   ├── runWithAgentContext() ── AsyncLocalStorage 隔离
  │   └── query() ───── 主循环
  │
  ├── forkSubagent.ts ── Agent fork（创建子Agent的子Agent）
  │   ├── FORK_AGENT 常量
  │   ├── buildForkedMessages() ── 继承父上下文
  │   └── isForkSubagentEnabled()
  │
  └── 嵌套层级：
      Main REPL Agent
          └── Subagent（Agent Tool）
                └── Fork Subagent（再嵌套一层）
```

### agentContext.ts — AsyncLocalStorage 隔离机制

```typescript
// 关键设计：用 AsyncLocalStorage 解决并发 Agent 上下文污染
export const agentContext = new AsyncLocalStorage<AgentContext>()

// 在子 Agent 执行时注入上下文
runWithAgentContext(subagentContext, () => {
  return runAgent(params)  // 这个函数内的所有 async 调用都能访问 context
})

// 在任何地方获取当前 Agent 的上下文
const ctx = agentContext.getStore()
ctx?.agentId   // 当前 agent 的 UUID
ctx?.agentType  // 'subagent' | 'teammate'
```

### OpenClaw 运用方案

| 目标 | 具体任务 | 文件 |
|------|---------|------|
| Subagent 上下文隔离 | 引入 `AsyncLocalStorage` 解决多 subagent 上下文污染 | `openclaw/agent_context.py` |
| Subagent 嵌套 | 支持 Agent 调用 Agent（目前只支持一层） | `openclaw/subagent.py` |
| Worktree 隔离 | 引入 `git worktree` 隔离执行环境 | `openclaw/worktree.py` |
| 后台 Agent | 参考 `BackgroundTask` + `killAsyncAgent` 机制 | `openclaw/background.py` |
| Agent 生命周期 | spawn/resume/kill 完整状态机 | `openclaw/subagent.py` |

---

## 🎯 模块四：上下文系统（高优先级）
**文件**：`src/context.ts` | `src/utils/claudemd.ts` | `src/memdir/`

### 核心设计

```typescript
// context.ts - 对话启动时一次性收集
export const getSystemContext = memoize(async () => {
  const [gitStatus, envVars, ...] = await Promise.all([
    getGitStatus(),
    getRelevantEnvVars(),
    ...
  ])
  return {
    gitStatus,
    envVars,
    // ... 全部打包成一个 context 对象
  }
})

// memdir.ts - memory directory 管理
export class MemDir {
  // 扫描 MEMORY.md 和 memory/*.md
  findRelevantMemories(query: string): MemoryItem[]
  memoryScan(): void   // 启动时全量扫描
  memoryAge(): string  // 计算记忆"新鲜度"
}
```

### OpenClaw 运用方案

| 目标 | 具体任务 | 文件 |
|------|---------|------|
| 统一缓存层 | 重构 `context_cache.py`，参考 memoize 模式 | `openclaw/context_cache.py` |
| Memory 扫描 | 借鉴 `memdir.ts` 的 findRelevantMemories | `openclaw/memory.py` |
| claude.md | 参考 `claudemd.ts` 实现项目级上下文注入 | `openclaw/project_context.py` |

---

## 🎯 模块五：Hooks 系统（高优先级）
**文件**：`src/utils/hooks.ts`（5022行）| `src/types/hooks.ts`

### 架构拆解

```
hooks.ts - 5022行，Hooks 生命周期管理

核心概念：
- HookEvent: hook 可以触发的事件类型
- HookCallback: 钩子回调函数
- HookInput: 传递给钩子的输入
- HookJSONOutput: 钩子返回的数据

支持的 Hook 事件：
- beforeeverytasks
- aftereverytasksoutputs
- beforeeverymessageprompt
- aftereverycommandoutput
- ontoolcall  （工具调用时）
- onsearch   （搜索时）
- onreflection （反思时）
- onnotification （通知时）

注册方式：
1. 项目级：.claude/hooks.json
2. 用户级：~/.claude/hooks.json
3. 插件级：插件 hooks.json
```

### OpenClaw 运用方案

| 目标 | 具体任务 | 文件 |
|------|---------|------|
| OpenClaw Hooks | 实现 `on_trade` / `on_market_data` / `on_review` 等钩子 | `openclaw/hooks.py` |
| Skill Hooks | 参考 `registerSkillHooks.ts` 的 hook 注册机制 | `openclaw/tools/skill_tool.py` |
| 生命周期点 | 交易执行前后、市场数据获取后等关键点插入钩子 | `openclaw/hooks.py` |

---

## 🎯 模块六：状态管理系统（中优先级）
**文件**：`src/state/AppState.tsx` | `src/state/AppStateStore.ts`

### 架构拆解

```
AppState.tsx ──────── 全局状态（React 16.8之前的类组件模式）
  ├── sessionId: string
  ├── agentId: string
  ├── currentAgent: Agent
  ├── permissionMode: PermissionMode
  ├── settings: Settings
  ├── tasks: BackgroundTask[]
  ├── teammates: Teammate[]
  └── ...
    │
AppStateStore.ts ──── 响应式存储（类似 Redux）
    ├── getState(): AppState
    ├── setState(patch): void
    ├── subscribe(listener): unsubscribe
    └── useState() ──── React hook 集成
```

### OpenClaw 运用方案

| 目标 | 具体任务 | 文件 |
|------|---------|------|
| 状态中心 | 建立 `openclaw/state.py` 统一状态管理 | `openclaw/state.py` |
| 状态持久化 | 参考 sessionStorage，把状态写入磁盘 | `openclaw/state.py` |
| 订阅机制 | 实现类似 AppStateStore 的发布订阅 | `openclaw/state.py` |

---

## 🎯 模块七：MCP 系统（中优先级）
**文件**：`src/services/mcp/*.ts` | `src/tools/MCPTool/`

### 架构拆解

```
services/mcp/
├── client.ts ─────────── MCP 客户端核心
├── MCPConnectionManager.tsx ── 连接管理器
├── config.ts ─────────── MCP 服务器配置解析
├── types.ts ──────────── MCP 类型定义
├── normalization.ts ──── 工具名/参数规范化
├── channelNotification.ts ── 通道通知
├── elicitationHandler.ts ── 用户交互处理
├── oauthPort.ts ─────── OAuth 端口管理
├── officialRegistry.ts ─ 官方 MCP 注册表
└── xaa.ts / xaaIdpLogin.ts ── 特定集成

tools/MCPTool/
├── MCPTool.ts ────────── MCP 工具包装器
│   └── 把 MCP 工具接入 tool pool
└── UI.tsx ───────────── MCP 结果渲染
```

### MCP 连接流程

```
配置 MCP 服务器
    ↓
MCPConnectionManager.connect()
    ↓
创建 stdio / HTTP 传输
    ↓
MCP 握手协议
    ↓
tools/list → 获取工具列表
    ↓
normalize → 标准化工具名
    ↓
接入 assembleToolPool()
    ↓
用户可以调用 MCP 工具
```

### OpenClaw 运用方案

| 目标 | 具体任务 | 文件 |
|------|---------|------|
| MCP 客户端 | 参考 `client.ts` 重构 OpenClaw MCP | `openclaw/mcp/client.py` |
| 工具标准化 | 参考 `normalization.ts` 统一工具接口 | `openclaw/mcp/normalize.py` |
| MiniMax MCP | 已有 minimax-coding-plan-mcp，完善其接入 | `openclaw/mcp/minimax.py` |

---

## 🎯 模块八：命令系统（中优先级）
**文件**：`src/commands.ts`（500+行）| `src/commands/*/`

### 架构拆解

```
commands.ts ──────── 入口：注册所有 / 命令
  │
  ├── /commit ── commit.ts
  ├── /diff ──── diff/index.tsx
  ├── /config ── config/index.tsx
  ├── /doctor ── doctor/doctor.tsx
  ├── /mcp ───── mcp/index.ts
  ├── /compact ─ compact/compact.ts
  ├── /review ── review.ts
  ├── /session ─ session/index.tsx
  └── ... 共 70+ 命令

每个命令：
  ├── index.ts ──── 命令入口
  ├── CommandName.tsx ── React TUI 组件（可选）
  └── prompt.ts ─────── AI 提示词（可选）
```

### OpenClaw 运用方案

| 目标 | 具体任务 | 文件 |
|------|---------|------|
| 命令注册表 | 建立类似 commands.ts 的统一命令注册 | `openclaw/commands.py` |
| /review → /复盘 | 已有，但需改进交互 | `openclaw/commands/review.py` |
| /trade → /交易 | 新增 `/交易` 命令查询账户 | `openclaw/commands/trade.py` |
| /skill → /技能 | 新增 `/技能` 管理 skill | `openclaw/commands/skill.py` |

---

## 🎯 模块九：查询引擎（低优先级，长期）
**文件**：`src/query.ts`（~1000行）| `src/queryContext.ts`

### 架构拆解

```typescript
// query.ts - 主查询循环
async function query(
  messages: NormalizedMessage[],
  params: QueryParams
): Promise<QueryResult> {
  // 1. 构建 prompt
  // 2. 调用模型 API
  // 3. 处理响应（tool_use / text）
  // 4. 执行工具
  // 5. 渲染结果
  // 6. 循环直到完成
}
```

### OpenClaw 运用方案

| 目标 | 具体任务 | 文件 |
|------|---------|------|
| 交易决策引擎 | 参考 query 循环实现自动化交易决策 | `openclaw/trading/decision_engine.py` |
| 工具调用循环 | 参考 tool use 处理实现工具执行器 | `openclaw/tools/executor.py` |

---

## 📋 完整执行计划

### 第一阶段：工具系统 + 权限安全（1-3天）

**目标**：把 OpenClaw 的工具系统升级到 Claude Code 水平

| 时间 | 任务 | 交付物 |
|------|------|--------|
| Day 1 AM | 完成 `BaseTool` 基类 + `ToolRegistry` 集成到 app.py | `openclaw/tools/base.py` |
| Day 1 PM | 引入权限规则系统，建立 `PermissionRule` + `PermissionMode` | `openclaw/tools/security.py` |
| Day 1 PM | 编写危险命令库（参考 bashPermissions.ts）| `openclaw/tools/dangerous_patterns.py` |
| Day 2 AM | 重构 skill 加载（参考 SkillTool.ts）| `openclaw/tools/skill_tool.py` |
| Day 2 PM | 建立工具测试框架，验证所有工具 | 测试覆盖 |
| Day 3 | 代码 review + 提交 Git | PR |

### 第二阶段：Agent 系统 + 上下文缓存（4-6天）

**目标**：实现 subagent 嵌套和统一缓存

| 时间 | 任务 | 交付物 |
|------|------|--------|
| Day 4 | 引入 `agent_context.py`（AsyncLocalStorage）| 并发安全 |
| Day 4 | 实现 subagent spawn/resume/kill | `openclaw/subagent.py` |
| Day 5 | 重构 `context_cache.py`（参考 context.ts memoize）| 缓存命中率提升 |
| Day 5 | 实现 Memory 扫描（参考 memdir.ts）| `openclaw/memory.py` |
| Day 6 | 集成到 app.py + 测试 | 完整演示 |

### 第三阶段：Hooks 系统 + 命令系统（7-8天）

**目标**：开放扩展性，支持用户自定义钩子

| 时间 | 任务 | 交付物 |
|------|------|--------|
| Day 7 | 实现 `openclaw/hooks.py`（Hook 注册+执行）| 钩子框架 |
| Day 7 | 实现 `on_trade` / `on_market_data` 钩子 | 交易钩子 |
| Day 8 | 建立命令注册表 + `/复盘` / `/交易` 命令 | `openclaw/commands.py` |

### 第四阶段：状态管理 + MCP（9-10天）

**目标**：完善状态管理和 MCP 支持

| 时间 | 任务 | 交付物 |
|------|------|--------|
| Day 9 | 重构 `state.py`（发布订阅+持久化）| 状态框架 |
| Day 10 | 完善 MiniMax MCP 接入 + 图片理解测试 | 完整功能 |

---

## 🔑 最核心的 5 个设计模式（必须掌握）

1. **buildTool 工厂模式** — 工具定义标准化，input/output schema 分离
2. **AsyncLocalStorage 上下文隔离** — 并发 Agent 不互相干扰
3. **PermissionRule 规则引擎** — 可配置的权限决策系统
4. **memoize 缓存** — 对话期间零重复 I/O
5. **工具注册表 + 动态条件** — Feature Flag 控制工具可用性

---

## 📁 已读完的文件清单（本次）

```
✅ src/entrypoints/cli.tsx            302行
✅ src/tools.ts                       ~3500行
✅ src/Tool.ts                        ~1000行
✅ src/context.ts                     ~500行
✅ src/utils/agentContext.ts           178行
✅ src/tools/AgentTool/AgentTool.tsx  1397行
✅ src/tools/BashTool/bashPermissions.ts 2621行
✅ src/tools/SkillTool/SkillTool.ts  ~1000行
✅ src/main.tsx                       ~500行（部分）
✅ src/commands.ts                     ~500行（部分）
✅ src/utils/hooks.ts                 ~500行（部分）
✅ src/utils/permissions/PermissionRule.ts ~200行（部分）
✅ src/utils/permissions/bashClassifier.ts ~300行（部分）
✅ README.md + third-party-models.md
```

---

*计划版本：v2.0 | 更新日期：2026-04-03 | 状态：待执行*
