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
| 39 | 数据验证器 | `src/utils/settings/validation.ts` | validators.py | ✅ |
| 40 | 异步工具 | async patterns | async_utils.py | ✅ |
| 41 | Cron调度 | `src/utils/cron.ts` | cron.py | ✅ |
| 42 | 限流器 | rate limiting | rate_limit.py | ✅ |
| 43 | Abort控制器 | `src/utils/abortController.ts` | abort.py | ✅ |
| 44 | 睡眠工具 | `src/utils/sleep.ts` | sleep.py | ✅ |
| 45 | 数组工具 | `src/utils/array.ts` | array_utils.py | ✅ |
| 46 | 字符串工具 | `src/utils/stringUtils.ts` | string_utils.py | ✅ |
| 47 | 路径工具 | `src/utils/path.ts` | path_utils.py | ✅ |
| 48 | 文件工具 | `src/utils/file.ts` | file_utils.py | ✅ |
| 49 | 调试工具 | `src/utils/debug.ts` | debug_utils.py | ✅ |
| 50 | YAML处理 | `src/utils/yaml.ts` | yaml_utils.py | ✅ |
| 51 | 进程工具 | `src/utils/process.ts` | process_utils.py | ✅ |
| 52 | 命令查找 | `src/utils/which.ts` | which.py | ✅ |
| 53 | XDG目录 | `src/utils/xdg.ts` | xdg.py | ✅ |
| 54 | 随机单词 | `src/utils/words.ts` | words.py | ✅ |
| 55 | 哈希工具 | `src/utils/hash.ts` | hash_utils.py | ✅ |
| 56 | HTTP工具 | `src/utils/http.ts` | http_utils.py | ✅ |
| 57 | 加密工具 | `src/services/oauth/crypto.ts` | crypto_utils.py | ✅ |
| 58 | 活动管理 | `src/utils/activityManager.ts` | activity_manager.py | ✅ |
| 59 | 提示词模板 | prompt system | prompt.py | ✅ |

## 更新规则
每次学习完一个模块，在此文件更新"当前模块"为下一个

## 第60批（2026-04-04 08:30）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 60 | 顾问系统 | `src/utils/advisor.ts` | advisor.py | ✅ |
| 61 | 智能会话搜索 | `src/utils/agenticSessionSearch.ts` | agentic_search.py | ✅ |
| 62 | 上下文分析 | `src/utils/analyzeContext.ts` | context_analyzer.py | ✅ |

## 第61批（2026-04-04 08:35）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 63 | 附件系统 | `src/utils/attachments.ts` | attachments.py | ✅ |

## 第62批（2026-04-04 08:40）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 64 | 边查询API | `src/utils/sideQuery.ts` | side_query.py | ✅ |
| 65 | 慢操作日志 | `src/utils/slowOperations.ts` | slow_operations.py | ✅ |

## 第63批（2026-04-04 08:43）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 66 | 会话存储 | `src/utils/sessionStorage.ts` | session_storage.py | ✅ |
| 67 | 文件历史 | `src/utils/fileHistory.ts` | file_history.py | ✅ |

## 第64批（2026-04-04 08:50）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 68 | 工作目录 | `src/utils/cwd.ts` | cwd.py | ✅ |
| 69 | 环境变量 | `src/utils/envUtils.ts` | env_utils.py | ✅ |
| 70 | 路径工具 | `src/utils/path.ts` | path_utils.py | ✅ |

## 第65批（2026-04-04 08:53）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 71 | 格式化工具 | `src/utils/format.ts` | format.py | ✅ |
| 72 | 字符串工具 | `src/utils/stringUtils.ts` | string_utils.py | ✅ |

## 第66批（2026-04-04 08:56）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 73 | JSON工具 | `src/utils/json.ts` | json_utils.py | ✅ |
| 74 | 日志工具 | `src/utils/log.ts` | log.py | ✅ |

## 第67批（2026-04-04 09:00）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 75 | 缓存工具 | `src/utils/memoize.ts` | memoize.py | ✅ |
| 76 | 中断控制器 | `src/utils/abortController.ts` | abort_controller.py | ✅ |

## 第68批（2026-04-04 09:03）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 77 | 命令查找 | `src/utils/which.ts` | which.py | ✅ |
| 78 | 进程执行 | `src/utils/execFileNoThrow.ts` | exec_utils.py | ✅ |

## 第69批（2026-04-04 09:06）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 79 | 显示标签 | `src/utils/displayTags.ts` | display_tags.py | ✅ |
| 80 | 数组工具 | `src/utils/array.ts` | array_utils.py | ✅ |

## 第70批（2026-04-04 09:10）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 81 | 二进制检查 | `src/utils/binaryCheck.ts` | binary_check.py | ✅ |
| 82 | UUID工具 | `src/utils/uuid.ts` | uuid_utils.py | ✅ |

## 第71批（2026-04-04 09:13）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 83 | 清理注册表 | `src/utils/cleanupRegistry.ts` | cleanup_registry.py | ✅ |
| 84 | 错误类 | `src/utils/errors.ts` | errors.py | ✅ |

## 第72批（2026-04-04 09:16）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 85 | Beta特性管理 | `src/utils/betas.ts` | betas.py | ✅ |

## 第73批（2026-04-04 09:20）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 86 | API提供者 | `src/utils/model/providers.ts` | providers.py | ✅ |
| 87 | 平台检测 | `src/utils/platform.ts` | platform.py | ✅ |

## 第74批（2026-04-04 09:22）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 88 | 缓存路径 | `src/utils/cachePaths.ts` | cache_paths.py | ✅ |

## 第75批（2026-04-04 09:24）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 89 | 哈希工具 | `src/utils/hash.ts` | hash_utils.py | ✅ |

## 第76批（2026-04-04 09:26）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 90 | 字符串截断 | `src/utils/truncate.ts` | truncate.py | ✅ |

## 第77批（2026-04-04 09:28）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 91 | 环形缓冲区 | `src/utils/CircularBuffer.ts` | circular_buffer.py | ✅ |

## 第78批（2026-04-04 09:30）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 92 | 归属文本 | `src/utils/attribution.ts` | attribution.py | ✅ |

## 第79批（2026-04-04 09:33）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 93 | 活动管理器 | `src/utils/activityManager.ts` | activity_manager.py | ✅ |

## 第80批（2026-04-04 09:35）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 94 | Agent团队开关 | `src/utils/agentSwarmsEnabled.ts` | agent_swarms.py | ✅ |
| 95 | 参数替换 | `src/utils/argumentSubstitution.ts` | argument_substitution.py | ✅ |

## 第81批（2026-04-04 09:37）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 96 | 终端录制 | `src/utils/asciicast.ts` | asciicast.py | ✅ |

## 第82批（2026-04-04 09:40）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 97 | 缓冲写入器 | `src/utils/bufferedWriter.ts` | buffered_writer.py | ✅ |

## 第83批（2026-04-04 09:42）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 98 | 调试日志 | `src/utils/debug.ts` | debug.py | ✅ |

## 第84批（2026-04-04 09:45）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 99 | Agent标识 | `src/utils/agentId.ts` | agent_id.py | ✅ |
| 100 | Claude提示协议 | `src/utils/claudeCodeHints.ts` | claude_code_hints.py | ✅ |

## 第85批（2026-04-04 09:48）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 101 | Signal信号 | `src/utils/signal.ts` | signal.py | ✅ |
| 102 | CA证书 | `src/utils/caCerts.ts` | ca_certs.py | ✅ |

## 第86批（2026-04-04 09:50）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 103 | AWS工具 | `src/utils/aws.ts` | aws_utils.py | ✅ |
| 104 | Claude桌面配置 | `src/utils/claudeDesktop.ts` | claude_desktop.py | ✅ |

## 第87批（2026-04-04 09:52）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 105 | 运行时检测 | `src/utils/bundledMode.ts` | bundled_mode.py | ✅ |
| 106 | 记忆文件加载 | `src/utils/claudemd.ts` | claude_md.py | ✅ |

## 第88批（2026-04-04 09:54）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 107 | Ripgrep封装 | `src/utils/ripgrep.ts` | ripgrep.py | ✅ |
| 108 | 进程工具 | `src/utils/process.ts` | process_utils.py | ✅ |

## 第89批（2026-04-04 09:56）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 109 | 国际化 | `src/utils/intl.ts` | intl.py | ✅ |
| 110 | Diff | `src/utils/diff.ts` | diff.py | ✅ |

## 第90批（2026-04-04 09:58）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 111 | 文件工具 | `src/utils/file.ts` | file_utils.py | ✅ |
| 112 | 查找可执行文件 | `src/utils/findExecutable.ts` | find_executable.py | ✅ |

## 第91批（2026-04-04 10:00）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 113 | Git工具 | `src/utils/git.ts` | git_utils.py | ✅ |
| 114 | Frontmatter解析 | `src/utils/frontmatterParser.ts` | frontmatter_parser.py | ✅ |

## 第92批（2026-04-04 10:02）
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 115 | YAML解析 | `src/utils/yaml.ts` | yaml.py | ✅ |
| 116 | Zod转JSON Schema | `src/utils/zodToJsonSchema.ts` | zod_to_json_schema.py | ✅ |

## 第93批（2026-04-04 10:04】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 117 | Token计算 | `src/utils/tokens.ts` | tokens.py | ✅ |

## 第94批（2026-04-04 10:05】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 118 | API预连接 | `src/utils/apiPreconnect.ts` | api_preconnect.py | ✅ |

## 第95批（2026-04-04 10:07】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 119 | 便携认证 | `src/utils/authPortable.ts` | auth_portable.py | ✅ |

## 第96批（2026-04-04 10:08】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 120 | 文件锁 | `src/utils/lockfile.ts` | lockfile.py | ✅ |

## 第97批（2026-04-04 10:10】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 121 | 文件操作分析 | `src/utils/fileOperationAnalytics.ts` | file_operation_analytics.py | ✅ |

## 第98批（2026-04-04 10:12】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 122 | 模型别名 | `src/utils/modelStrings.ts` | model_strings.py | ✅ |
| 123 | 模型允许列表 | `src/utils/modelAllowlist.ts` | model_allowlist.py | ✅ |

## 第99批（2026-04-04 10:14】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 124 | 顺序执行 | `src/utils/sequential.ts` | sequential.py | ✅ |
| 125 | 异步工具 | `src/utils/async.ts` | async_utils.py | ✅ |

## 第100批（2026-04-04 10:15】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 126 | Result类型 | `src/utils/result.ts` | result.py | ✅ |
| 127 | Option类型 | `src/utils/option.ts` | option.py | ✅ |

## 第101批（2026-04-04 10:17】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 128 | 类型守卫 | `src/utils/typeGuards.ts` | type_guards.py | ✅ |
| 129 | 超时工具 | `src/utils/timeout.ts` | timeout.py | ✅ |

## 第102批（2026-04-04 10:18】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 130 | 功能开关 | `src/utils/flags.ts` | flags.py | ✅ |
| 131 | 重试工具 | `src/utils/retry.ts` | retry.py | ✅ |

## 第103批（2026-04-04 10:20】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 132 | 上下文窗口 | `src/utils/context.ts` | context.py | ✅ |
| 133 | 事件系统 | `src/utils/events.ts` | events.py | ✅ |

## 第104批（2026-04-04 10:22】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 134 | 指标收集器 | `src/utils/metrics.ts` | metrics.py | ✅ |
| 135 | 对象池 | `src/utils/pool.ts` | pool.py | ✅ |

## 第105批（2026-04-04 10:24】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 136 | 堆结构 | `src/utils/heap.ts` | heap.py | ✅ |
| 137 | LRU缓存 | `src/utils/lruCache.ts` | lru_cache.py | ✅ |

## 第106批（2026-04-04 10:26】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 138 | 限流器 | `src/utils/rateLimit.ts` | rate_limit.py | ✅ |
| 139 | 单次执行 | `src/utils/once.ts` | once.py | ✅ |

## 第107批（2026-04-04 10:28】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 140 | 采样器 | `src/utils/sampler.ts` | sampler.py | ✅ |
| 141 | 限流状态管理 | `src/utils/rateLimitReset.ts` | rate_limit_reset.py | ✅ |

## 第108批（2026-04-04 10:30】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 142 | 异步流 | `src/utils/stream.ts` | stream.py | ✅ |
| 143 | 缓冲区 | `src/utils/buffer.ts` | buffer.py | ✅ |

## 第109批（2026-04-04 10:32】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 144 | 模板引擎 | `src/utils/template.ts` | template.py | ✅ |
| 145 | 数据转换 | `src/utils/transform.ts` | transform.py | ✅ |

## 第110批（2026-04-04 10:33】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 146 | 数据验证 | `src/utils/validate.ts` | validate.py | ✅ |
| 147 | UUID工具 | `src/utils/uuid.ts` | uuid.py | ✅ |

## 第111批（2026-04-04 10:35】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 148 | 文件监控 | `src/utils/watch.ts` | watch.py | ✅ |
| 149 | 确保执行一次 | `src/utils/onceMore.ts` | once_more.py | ✅ |

## 第112批（2026-04-04 10:48】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 150 | 延迟计算 | `src/utils/deferred.ts` | deferred.py | ✅ |
| 151 | 弱引用缓存 | `src/utils/weakCache.ts` | weak_cache.py | ✅ |
| 152 | 批量处理 | `src/utils/batch.ts` | batch.py | ✅ |

## 第113批（2026-04-04 10:50】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 153 | 队列 | `src/utils/queue.ts` | queue.py | ✅ |
| 154 | 栈 | `src/utils/stack.ts` | stack.py | ✅ |
| 155 | 树 | `src/utils/tree.ts` | tree.py | ✅ |

## 第114批（2026-04-04 10:52】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 156 | 图 | `src/utils/graph.ts` | graph.py | ✅ |
| 157 | 跳表 | `src/utils/skipList.ts` | skiplist.py | ✅ |
| 158 | 布隆过滤器 | `src/utils/bloomFilter.ts` | bloomfilter.py | ✅ |

## 第115批（2026-04-04 10:54】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 159 | 压缩 | `src/utils/compression.ts` | compression.py | ✅ |
| 160 | 加密 | `src/utils/crypto.ts` | crypto.py | ✅ |
| 161 | 编码 | `src/utils/encoding.ts` | encoding.py | ✅ |

## 第116批（2026-04-04 10:56】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 162 | 解析器 | `src/utils/parser.ts` | parser.py | ✅ |
| 163 | 序列化 | `src/utils/serializer.ts` | serializer.py | ✅ |

## 第117批（2026-04-04 10:58】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 164 | ID生成器 | `src/utils/idGenerator.ts` | id_generator.py | ✅ |
| 165 | 缓存 | `src/utils/cache.ts` | cache.py | ✅ |
| 166 | 调度器 | `src/utils/scheduler.ts` | scheduler.py | ✅ |

## 第118批（2026-04-04 11:00】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 167 | 计数器 | `src/utils/counter.ts` | counter.py | ✅ |
| 168 | 限流器 | `src/utils/limiter.ts` | limiter.py | ✅ |
| 169 | 断路器 | `src/utils/circuitBreaker.ts` | breaker.py | ✅ |

## 第119批（2026-04-04 11:02】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 170 | 分布式锁 | `src/utils/lock.ts` | lock.py | ✅ |
| 171 | 令牌桶漏桶 | `src/utils/bucket.ts` | bucket.py | ✅ |

## 第120批（2026-04-04 11:04】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 172 | 过滤器 | `src/utils/filter.ts` | filter.py | ✅ |
| 173 | 键路径 | `src/utils/keyPath.ts` | keypath.py | ✅ |
| 174 | 函数式 | `src/utils/functools.ts` | functools.py | ✅ |

## 第121批（2026-04-04 11:05】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 175 | 异步队列 | `src/utils/asyncQueue.ts` | async_queue.py | ✅ |
| 176 | 异步池 | `src/utils/asyncPool.ts` | async_pool.py | ✅ |

## 第122批（2026-04-04 11:07】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 177 | 防抖节流 | `src/utils/debounce.ts` | debounce.py | ✅ |
| 178 | 异步工具2 | `src/utils/asyncUtils2.ts` | async_utils2.py | ✅ |

## 第123批（2026-04-04 11:09】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 179 | 连接管理 | `src/utils/connection.ts` | connection.py | ✅ |
| 180 | 退避策略 | `src/utils/backoff.ts` | backoff.py | ✅ |

## 第124批（2026-04-04 11:11】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 181 | 异步监控 | `src/utils/asyncWatcher.ts` | async_watcher.py | ✅ |
| 182 | 弹性模式 | `src/utils/resilience.ts` | resilience.py | ✅ |

## 第125批（2026-04-04 11:13】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 183 | 共享值 | `src/utils/shared.ts` | shared.py | ✅ |
| 184 | 追踪 | `src/utils/trace.ts` | trace.py | ✅ |

## 第126批（2026-04-04 11:15】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 185 | 指标 | `src/utils/metric.ts` | metric.py | ✅ |
| 186 | 事件发射 | `src/utils/emit.ts` | emit.py | ✅ |

## 第127批（2026-04-04 11:17】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 187 | 限流2 | `src/utils/rateLimit2.ts` | ratelimit2.py | ✅ |
| 188 | 限流3 | `src/utils/rateLimit3.ts` | ratelimit3.py | ✅ |

## 第128批（2026-04-04 11:19】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 189 | 严格模式 | `src/utils/strict.ts` | strict.py | ✅ |
| 190 | 克隆 | `src/utils/clone.ts` | clone.py | ✅ |

## 第129批（2026-04-04 11:21】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 191 | 时间工具 | `src/utils/time.ts` | time.py | ✅ |
| 192 | 字符串工具 | `src/utils/string.ts` | string.py | ✅ |

## 第130批（2026-04-04 11:23】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 193 | 随机工具 | `src/utils/random.ts` | random.py | ✅ |
| 194 | 正则工具 | `src/utils/regex.ts` | regex.py | ✅ |

## 第131批（2026-04-04 11:25】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 195 | 颜色工具 | `src/utils/color.ts` | color.py | ✅ |
| 196 | 数字工具 | `src/utils/number.ts` | number.py | ✅ |

## 第132批（2026-04-04 11:27】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 197 | 验证器 | `src/utils/validate.ts` | validate.py | ✅ |
| 198 | 环境变量 | `src/utils/env.ts` | env.py | ✅ |

## 第133批（2026-04-04 11:30】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 199 | JSON工具 | `src/utils/json.ts` | json.py | ✅ |
| 200 | 文件工具 | `src/utils/file.ts` | file.py | ✅ |
| 201 | 路径工具 | `src/utils/path.ts` | path.py | ✅ |

## 第134批（2026-04-04 11:32】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 202 | 控制台 | `src/utils/console.ts` | console.py | ✅ |
| 203 | 进度条 | `src/utils/progress.ts` | progress.py | ✅ |
| 204 | 表格 | `src/utils/table.ts` | table.py | ✅ |

## 第135批（2026-04-04 11:34】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 205 | 断言 | `src/utils/assert.ts` | assert.py | ✅ |
| 206 | 错误 | `src/utils/error.ts` | error.py | ✅ |
| 207 | 调试 | `src/utils/debug.ts` | debug.py | ✅ |

## 第136批（2026-04-04 11:36】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 208 | 批处理 | `src/utils/batch.ts` | batch.py | ✅ |
| 209 | 合并工具 | `src/utils/merge.ts` | merge.py | ✅ |
| 210 | 对象池2 | `src/utils/pool2.ts` | pool2.py | ✅ |

## 第137批（2026-04-04 11:38】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 211 | 切片工具 | `src/utils/slice.ts` | slice.py | ✅ |
| 212 | 转换工具 | `src/utils/transform2.ts` | transform2.py | ✅ |
| 213 | 异步迭代 | `src/utils/asyncIter.ts` | async_iter.py | ✅ |

## 第138批（2026-04-04 11:40】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 214 | 弱引用 | `src/utils/weak.ts` | weak.py | ✅ |
| 215 | 最终化 | `src/utils/finalization.ts` | finalization.py | ✅ |
| 216 | 结构体 | `src/utils/struct.ts` | struct.py | ✅ |

## 第139批（2026-04-04 11:42】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 217 | 原子化 | `src/utils/atom.ts` | atom.py | ✅ |
| 218 | 引用 | `src/utils/ref.ts` | ref.py | ✅ |
| 219 | 信号 | `src/utils/signal.ts` | signal.py | ✅ |

## 第140批（2026-04-04 11:44】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 220 | 存储 | `src/utils/store.ts` | store.py | ✅ |
| 221 | 记忆化 | `src/utils/memo.ts` | memo.py | ✅ |
| 222 | 中间件 | `src/utils/middleware.ts` | middleware.py | ✅ |

## 第141批（2026-04-04 12:00】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 223 | LRU缓存 | `src/utils/lruCache.ts` | lru_cache.py | ✅ |
| 224 | 延迟对象 | `src/utils/deferred.ts` | deferred.py | ✅ |
| 225 | await工具 | `src/utils/awaiter.ts` | awaiter.py | ✅ |

## 第142批（2026-04-04 12:05】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 226 | 归约器 | `src/utils/reducer.ts` | reducer.py | ✅ |
| 227 | 映射器 | `src/utils/mapper.ts` | mapper.py | ✅ |
| 228 | 依赖解析 | `src/utils/resolver.ts` | resolver.py | ✅ |

## 第143批（2026-04-04 12:08】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 229 | 累加器 | `src/utils/accumulator.ts` | accumulator.py | ✅ |
| 230 | 构建器 | `src/utils/builder.ts` | builder.py | ✅ |
| 231 | 注册表 | `src/utils/registry.ts` | registry.py | ✅ |

## 第144批（2026-04-04 12:10】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 232 | 观察者 | `src/utils/observer.ts` | observer.py | ✅ |
| 233 | 状态机 | `src/utils/state.ts` | state.py | ✅ |
| 234 | 流程控制 | `src/utils/flow.ts` | flow.py | ✅ |

## 第145批（2026-04-04 12:12】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 235 | 模板2 | `src/utils/template2.ts` | template2.py | ✅ |
| 236 | 格式化 | `src/utils/format.ts` | format.py | ✅ |

## 第146批（2026-04-04 12:14】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 237 | 解析 | `src/utils/parse.ts` | parse.py | ✅ |
| 238 | 转换 | `src/utils/convert.ts` | convert.py | ✅ |

## 第147批（2026-04-04 12:16】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 239 | 异步池 | `src/utils/pool3.ts` | pool3.py | ✅ |
| 240 | 守卫 | `src/utils/guard.ts` | guard.py | ✅ |

## 第148批（2026-04-04 12:18】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 241 | 可选值 | `src/utils/optional.ts` | optional.py | ✅ |
| 242 | 结果类型 | `src/utils/result.ts` | result.py | ✅ |

## 第149批（2026-04-04 12:20】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 243 | 字典树 | `src/utils/trie.ts` | trie.py | ✅ |
| 244 | 环形缓冲区 | `src/utils/ring.ts` | ring.py | ✅ |

## 第150批（2026-04-04 12:22】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 245 | 矩阵 | `src/utils/matrix.ts` | matrix.py | ✅ |
| 246 | 区间 | `src/utils/interval.ts` | interval.py | ✅ |

## 第151批（2026-04-04 13:00】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 247 | 堆 | `src/utils/heap.ts` | heap.py | ✅ |
| 248 | 版本 | `src/utils/version.ts` | version.py | ✅ |
| 249 | YAML | `src/utils/yaml.ts` | yaml.py | ✅ |

## 第152批（2026-04-04 13:05】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 250 | TOML解析 | `src/utils/toml.ts` | toml.py | ✅ |
| 251 | URI工具 | `src/utils/uri.ts` | uri.py | ✅ |
| 252 | Base64 | `src/utils/base64.ts` | base64.py | ✅ |

## 第153批（2026-04-04 13:10】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 253 | 语义化版本 | `src/utils/semver.ts` | semver.py | ✅ |
| 254 | 差异计算 | `src/utils/diff.ts` | diff.py | ✅ |

## 第154批（2026-04-04 13:15】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 255 | 哈希 | `src/utils/hash.ts` | hash.py | ✅ |
| 256 | 令牌 | `src/utils/token.ts` | token.py | ✅ |

## 第155批（2026-04-04 13:17】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 257 | JWT | `src/utils/jwt.ts` | jwt.py | ✅ |
| 258 | UUID | `src/utils/uuid.ts` | uuid.py | ✅ |

## 第156批（2026-04-04 13:20】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 259 | 功能开关 | `src/utils/flags.ts` | flags.py | ✅ |
| 260 | 配置管理 | `src/utils/config.ts` | config.py | ✅ |

## 第157批（2026-04-04 13:22】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------| 
| 261 | 环境配置 | `src/utils/envConfig.ts` | env_config.py | ✅ |
| 262 | 模式验证 | `src/utils/schema.ts` | schema.py | ✅ |

## 第158批（2026-04-04 13:25】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 263 | 同步锁 | `src/utils/lock.ts` | lock.py | ✅ |
| 264 | 有序集合 | `src/utils/sorted.ts` | sorted.py | ✅ |
| 265 | 位操作 | `src/utils/bits.ts` | bits.py | ✅ |

## 第159批（2026-04-04 13:28】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 266 | 循环缓冲 | `src/utils/circular.ts` | circular.py | ✅ |
| 267 | 单子 | `src/utils/monad.ts` | monad.py | ✅ |
| 268 | 管道 | `src/utils/pipe.ts` | pipe.py | ✅ |

## 第160批（2026-04-04 13:30】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 269 | 双向映射 | `src/utils/biMap.ts` | bimap.py | ✅ |
| 270 | 数字工具 | `src/utils/numbers.ts` | numbers.py | ✅ |

## 第161批（2026-04-04 13:32】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 271 | 地理工具 | `src/utils/geo.ts` | geo.py | ✅ |
| 272 | 线条 | `src/utils/line.ts` | line.py | ✅ |

## 第162批（2026-04-04 13:35】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 273 | 范围 | `src/utils/range.ts` | range.py | ✅ |
| 274 | 时间 | `src/utils/time.ts` | time.py | ✅ |

## 第163批（2026-04-04 13:37】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 275 | 标识符 | `src/utils/id.ts` | id.py | ✅ |
| 276 | 单次执行 | `src/utils/once.ts` | once.py | ✅ |

## 第164批（2026-04-04 13:40】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 277 | 日志 | `src/utils/log.ts` | log.py | ✅ |
| 278 | 属性 | `src/utils/prop.ts` | prop.py | ✅ |

## 第165批（2026-04-04 14:50】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 279 | 环境变量 | `src/utils/env.ts` | env.py | ✅ |
| 280 | 文件系统 | `src/utils/fs.ts` | fs.py | ✅ |
| 281 | 路径 | `src/utils/path.ts` | path.py | ✅ |

## 第166批（2026-04-04 14:53】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 282 | 断言 | `src/utils/assert.ts` | assert2.py | ✅ |
| 283 | 延迟 | `src/utils/sleep.ts` | sleep.py | ✅ |
| 284 | 随机 | `src/utils/random.ts` | random2.py | ✅ |

## 第167批（2026-04-04 14:55】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 285 | 重试 | `src/utils/retry.ts` | retry2.py | ✅ |
| 286 | 超时 | `src/utils/timeout.ts` | timeout.py | ✅ |
| 287 | 加密 | `src/utils/crypto.ts` | crypto2.py | ✅ |

## 第168批（2026-04-04 14:57】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 288 | 防抖 | `src/utils/debounce.ts` | debounce.py | ✅ |
| 289 | 节流 | `src/utils/throttle.ts` | throttle2.py | ✅ |
| 290 | 批处理 | `src/utils/batch.ts` | batch2.py | ✅ |

## 第169批（2026-04-04 15:00】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 291 | 缓冲区 | `src/utils/buffer.ts` | buffer.py | ✅ |
| 292 | 插槽 | `src/utils/slot.ts` | slot.py | ✅ |
| 293 | 等待 | `src/utils/wait.ts` | wait.py | ✅ |

## 第170批（2026-04-04 15:03】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 294 | 对象池 | `src/utils/pool.ts` | pool.py | ✅ |
| 295 | 分组 | `src/utils/group.ts` | group.py | ✅ |
| 296 | 索引 | `src/utils/index.ts` | index.py | ✅ |

## 第171批（2026-04-04 15:05】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 297 | 压缩 | `src/utils/zip.ts` | zip.py | ✅ |
| 298 | 解码 | `src/utils/decode.ts` | decode.py | ✅ |
| 299 | 编码 | `src/utils/encode.ts` | encode.py | ✅ |

## 第172批（2026-04-04 15:08】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 300 | 堆 | `src/utils/heap.ts` | heap2.py | ✅ |
| 301 | 缓存 | `src/utils/cache.ts` | cache2.py | ✅ |
| 302 | 计数器 | `src/utils/counter.ts` | counter.py | ✅ |

## 第173批（2026-04-04 15:10】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 303 | 背包 | `src/utils/bag.ts` | bag.py | ✅ |
| 304 | 栈 | `src/utils/stack.ts` | stack.py | ✅ |
| 305 | 队列 | `src/utils/queue.ts` | queue2.py | ✅ |

## 第174批（2026-04-04 15:13】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 306 | 集合 | `src/utils/set.ts` | set2.py | ✅ |
| 307 | 映射 | `src/utils/map.ts` | map2.py | ✅ |
| 308 | 双端队列 | `src/utils/deque.ts` | deque.py | ✅ |

## 第175批（2026-04-04 15:15】
| # | 模块 | 源码文件 | 落地 | 状态 |
|---|------|---------|------|------|
| 309 | 列表 | `src/utils/list.ts` | list2.py | ✅ |
| 310 | 作用域 | `src/utils/scope.ts` | scope.py | ✅ |
| 311 | 记忆化 | `src/utils/memo.ts` | memo.py | ✅ |
