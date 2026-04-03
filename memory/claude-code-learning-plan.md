# Claude Code 源码学习计划

## 学习目标
通过深度研究 Claude Code 源码，将可落地的设计应用到 OpenClaw，提升系统的模块化程度、启动性能和工具扩展性。

---

## 第一阶段：Feature Flag 系统（高优先级）
**目标**：给 OpenClaw 加上 build-time feature flag 机制

**参考 Claude Code**：`bun:bundle` 的 `feature()` 宏 + 环境变量双重门控

**待研究文件**：
- `cc-haha-main/src/utils/envUtils.ts` — isEnvTruthy
- `cc-haha-main/src/bootstrap/state.ts` — 功能开关状态

**落地任务**：
- [ ] 在 OpenClaw 建立 `openclaw/feature_flags.py`
- [ ] 实现 `is_feature_enabled(name)` 函数
- [ ] 给 cron、MCP、交易模块等加上 feature flag
- [ ] 让不常用的模块按需加载

---

## 第二阶段：上下文缓存（高优先级）
**目标**：减少每次对话重复的文件 I/O

**参考 Claude Code**：`context.ts` 用 `memoize` 缓存 git/status/claude.md

**待研究文件**：
- `cc-haha-main/src/context.ts` — getGitStatus/getSystemContext memoize
- `cc-haha-main/src/utils/claudemd.ts` — memory file 读取

**落地任务**：
- [ ] 建立 `openclaw/context_cache.py` — 统一上下文缓存
- [ ] 把每日复盘、账户状态的重复读取改为缓存
- [ ] 写一个 `@cached` 装饰器

---

## 第三阶段：工具注册表（中优先级）
**目标**：统一管理所有工具的发现、注册、生命周期

**参考 Claude Code**：`tools.ts` 的 `getAllBaseTools()` + `getToolsForDefaultPreset()`

**待研究文件**：
- `cc-haha-main/src/tools.ts` — 工具注册表
- `cc-haha-main/src/Tool.ts` — buildTool 工厂函数

**落地任务**：
- [ ] 建立 `openclaw/tools/registry.py` — 统一工具注册表
- [ ] 把 app.py 里的路由改造为工具注册模式
- [ ] 支持工具的 `is_enabled()` 开关

---

## 第四阶段：并行预启动（低优先级）
**目标**：加速 OpenClaw Gateway 启动

**参考 Claude Code**：`main.tsx` 在模块加载前并行启动 MDM + Keychain 读取

**待研究文件**：
- `cc-haha-main/src/utils/startupProfiler.ts` — profileCheckpoint
- `cc-haha-main/src/utils/secureStorage/keychainPrefetch.ts`

**落地任务**：
- [ ] 在 gateway 启动时并行加载配置和初始化数据库
- [ ] 加上启动计时点便于诊断

---

## 第五阶段：Bash 权限模型（中优先级）
**目标**：学习 Claude Code 的 bash 命令安全过滤

**参考 Claude Code**：
- `BashTool/bashPermissions.ts` — 命令权限规则
- `BashTool/bashSecurity.ts` — 危险命令拦截
- `BashTool/readOnlyValidation.ts` — 只读模式校验

**待研究文件**：
- `cc-haha-main/src/tools/BashTool/bashPermissions.ts`
- `cc-haha-main/src/tools/BashTool/readOnlyValidation.ts`

**落地任务**：
- [ ] 审查 OpenClaw exec 工具的危险命令拦截
- [ ] 参考 Claude Code 的 permissionRule 系统

---

## 第六阶段：Subagent 层级（长期）
**目标**：实现 Agent 嵌套（复杂，暂定）

**参考 Claude Code**：`AgentTool.tsx` 的子 Agent 调度

**待研究文件**：
- `cc-haha-main/src/tools/AgentTool/runAgent.ts`
- `cc-haha-main/src/utils/agentContext.ts` — AsyncLocalStorage

**落地任务**：
- [ ] OpenClaw subagent 支持嵌套调用
- [ ] 用 AsyncLocalStorage 做上下文隔离

---

## 学习顺序
1. Feature Flag（最快落地）
2. Context 缓存（对交易系统价值高）
3. 工具注册表（结构优化）
4. Bash 权限模型（安全性）
5. 并行预启动（启动优化）
6. Subagent 层级（长期）

---

## 已读完的文件清单
- ✅ `src/entrypoints/cli.tsx` — CLI引导+快速路径
- ✅ `src/tools.ts` — 工具注册表
- ✅ `src/context.ts` — 系统上下文+memoize
- ✅ `src/tools/AgentTool/AgentTool.tsx` — 子Agent系统
- ✅ `src/tools/SkillTool/SkillTool.ts` — Skill执行
- ✅ `src/tools/BashTool/BashTool.tsx` — Shell执行
- ✅ `src/main.tsx` — 804KB主程序结构
- ✅ `src/utils/agentContext.ts` — AsyncLocalStorage上下文隔离
- ✅ `src/tools/BashTool/bashPermissions.ts` — 权限规则
- ✅ README.md / third-party-models.md — 架构文档
